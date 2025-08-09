import os
import boto3
from supabase import create_client

# ---------- AWS clients ----------
ssm_client = boto3.client("ssm")

# ---------- Config ----------
JOBS_PAGE_SIZE = int(os.environ.get("JOBS_PAGE_SIZE", "5000"))
WRITE_CHUNK = int(os.environ.get("WRITE_CHUNK", "1000"))

# ---------- Helpers ----------
def get_ssm_param(path: str) -> str:
    response = ssm_client.get_parameter(Name=path, WithDecryption=True)
    return response["Parameter"]["Value"]

def to_text(value):
    return "" if value is None else str(value)

def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i+size]

# ---------- Filter evaluator ----------
def eval_filter(filter_data: dict, job: dict) -> bool:
    filter_type = filter_data.get("type")
    field = filter_data.get("field")
    filter_value = filter_data.get("value") or {}
    haystack = job.get(field)

    # ----- Text -----
    if filter_type == "text_contains":
        return to_text(filter_value.get("q")) in to_text(haystack)
    if filter_type == "text_icontains":
        return to_text(filter_value.get("q")).lower() in to_text(haystack).lower()
    if filter_type == "text_not_contains":
        return to_text(filter_value.get("q")) not in to_text(haystack)
    if filter_type == "text_inot_contains":
        return to_text(filter_value.get("q")).lower() not in to_text(haystack).lower()
    if filter_type == "text_regex":
        import re
        try:
            return re.search(filter_value.get("pattern", ""), to_text(haystack)) is not None
        except re.error:
            return False

    # ----- Numbers -----
    try:
        haystack_number = float(haystack) if haystack is not None else None
    except (ValueError, TypeError):
        haystack_number = None

    if filter_type == "number_equals":
        return haystack_number == float(filter_value.get("value"))
    if filter_type == "number_not_equals":
        return haystack_number != float(filter_value.get("value"))
    if filter_type == "number_gt":
        return haystack_number is not None and haystack_number > float(filter_value.get("value"))
    if filter_type == "number_gte":
        return haystack_number is not None and haystack_number >= float(filter_value.get("value"))
    if filter_type == "number_lt":
        return haystack_number is not None and haystack_number < float(filter_value.get("value"))
    if filter_type == "number_lte":
        return haystack_number is not None and haystack_number <= float(filter_value.get("value"))
    if filter_type == "number_between":
        return (
            haystack_number is not None
            and float(filter_value.get("min")) <= haystack_number <= float(filter_value.get("max"))
        )

    # ----- Arrays -----
    if isinstance(haystack, list):
        if filter_type == "array_contains":
            return any(x in haystack for x in filter_value.get("any", []))
        if filter_type == "array_not_contains":
            return all(x not in haystack for x in filter_value.get("none", []))
        if filter_type == "array_length_gt":
            return len(haystack) > int(filter_value.get("value", 0))
        if filter_type == "array_length_lt":
            return len(haystack) < int(filter_value.get("value", 0))

    # ----- Boolean -----
    if filter_type == "bool_is":
        return bool(haystack) == bool(filter_value.get("value"))

    return False

def job_matches_all_filters(job: dict, filters: list[dict]) -> tuple[bool, list[bool]]:
    if not filters:
        return True, []
    results = [eval_filter(filter_item, job) for filter_item in filters]
    return all(results), results

# ---------- Supabase pulls ----------
def get_categories_for_user(supabase_client, user_id: int):
    response = supabase_client.table("categories").select("id,user_id,name,description").eq("user_id", user_id).execute()
    return response.data or []

def get_filters_for_category(supabase_client, category_id: int):
    # Join category_filter_relationship -> filters
    response = supabase_client.table("category_filter_relationship") \
        .select("mode, filters(id,user_id,name,field,type,value)") \
        .eq("category_id", category_id) \
        .execute()
    return response.data or []

def iter_all_jobs(supabase_client):
    start = 0
    while True:
        end = start + JOBS_PAGE_SIZE - 1
        response = supabase_client.table("unified_jobs").select("*").range(start, end).execute()
        rows = response.data or []
        if not rows:
            break
        for row in rows:
            yield row
        if len(rows) < JOBS_PAGE_SIZE:
            break
        start += JOBS_PAGE_SIZE

# ---------- Supabase writes ----------
def write_job_matches(supabase_client, rows: list[dict]):
    for group in chunked(rows, WRITE_CHUNK):
        supabase_client.table("job_matches").upsert(group, on_conflict="user_id,job_id").execute()

def write_filter_evaluations(supabase_client, rows: list[dict]):
    for group in chunked(rows, WRITE_CHUNK):
        supabase_client.table("filter_evaluations").insert(group).execute()

# ---------- Lambda handler ----------
def lambda_handler(event, context):
    user_id = event.get("user_id")
    if not user_id:
        raise ValueError("Missing user_id in event payload")

    supabase_url = get_ssm_param(os.environ["SUPABASE_URL_SSM_PATH"])
    supabase_key = get_ssm_param(os.environ["SUPABASE_KEY_SSM_PATH"])
    supabase_client = create_client(supabase_url, supabase_key)

    categories = get_categories_for_user(supabase_client, user_id)
    if not categories:
        return {
            "status": "success",
            "user_id": user_id,
            "message": "no categories found"
        }

    jobs = list(iter_all_jobs(supabase_client))
    jobs_scanned = len(jobs)

    total_matches = 0
    total_evaluations = 0

    for category in categories:
        filter_relationships = get_filters_for_category(supabase_client, category["id"])
        if not filter_relationships:
            continue

        inclusion_filters = [link["filters"] for link in filter_relationships if link["mode"] == "include"]
        exclusion_filters = [link["filters"] for link in filter_relationships if link["mode"] == "exclude"]

        job_match_rows = []
        filter_evaluation_rows = []

        for job in jobs:
            job_id = job["global_job_id"]

            inclusion_passed, inclusion_results = job_matches_all_filters(job, inclusion_filters)
            exclusion_results = [eval_filter(filter_item, job) for filter_item in exclusion_filters]
            has_exclusion_match = any(exclusion_results)

            if inclusion_passed and not has_exclusion_match:
                total_matches += 1
                job_match_rows.append({
                    "user_id": user_id,
                    "job_id": job_id,
                    "matched_filters": [f["id"] for f in inclusion_filters]
                })
            else:
                # Inclusion filter evaluations
                for filter_item, passed in zip(inclusion_filters, inclusion_results):
                    filter_evaluation_rows.append({
                        "user_id": user_id,
                        "filter_id": filter_item["id"],
                        "job_id": job_id,
                        "passed": bool(passed),
                        "reason": None
                    })
                # Exclusion filter evaluations
                for filter_item, passed in zip(exclusion_filters, exclusion_results):
                    filter_evaluation_rows.append({
                        "user_id": user_id,
                        "filter_id": filter_item["id"],
                        "job_id": job_id,
                        "passed": not bool(passed),  # pass means job wasn't excluded
                        "reason": None
                    })
                total_evaluations += len(inclusion_filters) + len(exclusion_filters)

        if job_match_rows:
            write_job_matches(supabase_client, job_match_rows)
        if filter_evaluation_rows:
            write_filter_evaluations(supabase_client, filter_evaluation_rows)

    return {
        "status": "success",
        "user_id": user_id,
        "jobs_scanned": jobs_scanned,
        "user_categories": len(categories),
        "job_matches_written": total_matches,
        "filter_evaluations_written": total_evaluations
    }
