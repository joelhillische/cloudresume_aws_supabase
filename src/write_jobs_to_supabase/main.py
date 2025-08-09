import os
import json
import boto3
from typing import Any, Dict, List, Optional
from supabase import create_client

# ---- AWS clients (init once per container) ----
s3 = boto3.client("s3")
ssm = boto3.client("ssm")

TABLE_NAME = os.environ.get("TABLE_NAME", "hirebase_jobs")

# ---- Helpers: AWS ----
def get_ssm_param(path: str) -> str:
    resp = ssm.get_parameter(Name=path, WithDecryption=True)
    return resp["Parameter"]["Value"]

def read_s3_json(bucket: str, key: str) -> dict:
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read())

def clean_text_value(v):
    """
    Returns a string or None.
    - str: trimmed
    - dict: use 'value' if present (common UI form pattern)
    - list/tuple: join non-empty items with ', '
    - bool/int/float: cast to str
    - else: None
    """
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s or None
    if isinstance(v, dict):
        val = v.get("value")
        return val.strip() if isinstance(val, str) and val.strip() else None
    if isinstance(v, (list, tuple)):
        parts = [str(x).strip() for x in v if x is not None and str(x).strip()]
        return ", ".join(parts) if parts else None
    if isinstance(v, (bool, int, float)):
        return str(v)
    return None


# ---- Helpers: locations (separate functions) ----
def extract_location_type(payload: Dict[str, Any]) -> Optional[str]:
    """Return the first non-empty location_type found (literal; no inference)."""
    lt = payload.get("location_type")
    if isinstance(lt, str) and lt.strip():
        return lt.strip()

    locations = payload.get("locations")
    if isinstance(locations, list):
        for loc in locations:
            if isinstance(loc, dict):
                for k in ("location_type", "type", "work_type", "workLocationType"):
                    v = loc.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
    elif isinstance(locations, dict):
        for k in ("location_type", "type", "work_type", "workLocationType"):
            v = locations.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None

def extract_country_list(locations: Any) -> Optional[List[str]]:
    """
    Collect *raw* country values (no normalization).
    - dicts: look for common country fields.
    - strings: assume 'City, Region, Country' → last segment.
    - Dedup + sort.
    """
    countries = set()

    def add_country(v: Any):
        if isinstance(v, str):
            s = v.strip()
            if s:
                countries.add(s)

    if isinstance(locations, list):
        for loc in locations:
            if isinstance(loc, dict):
                for k in ("country", "country_name", "countryName", "country_code", "countryCode"):
                    if k in loc:
                        add_country(loc[k])
            elif isinstance(loc, str):
                parts = [p.strip() for p in loc.split(",") if p.strip()]
                if parts:
                    add_country(parts[-1])
    elif isinstance(locations, dict):
        for k in ("country", "country_name", "countryName", "country_code", "countryCode"):
            if k in locations:
                add_country(locations[k])
    elif isinstance(locations, str):
        parts = [p.strip() for p in locations.split(",") if p.strip()]
        if parts:
            add_country(parts[-1])

    return sorted(countries) if countries else None

def map_row(j: dict) -> dict:
    row = {
        "hirebase_job_id": j.get("_id"),
        "company_name": clean_text_value(j.get("company_name")),  # fixes {"value": "..."}
        "job_title": clean_text_value(j.get("job_title")),
        "description_html": clean_text_value(j.get("description")),
        "locations": j.get("locations"),       # stays jsonb
        "salary_range": j.get("salary_range"), # stays jsonb
        "raw": j,
    }

    dp = clean_text_value(j.get("date_posted"))
    if isinstance(dp, str) and len(dp) == 10:
        row["date_posted"] = dp

    lt = extract_location_type(j)
    if lt:
        row["location_type"] = lt

    clist = extract_country_list(j.get("locations"))
    if clist:
        row["country_list"] = clist

    return row


# ---- Main handler ----
def lambda_handler(event, context):
    # SSM creds
    supabase_url_path = os.environ.get("SUPABASE_URL_SSM_PATH")
    supabase_key_path = os.environ.get("SUPABASE_KEY_SSM_PATH")
    if not supabase_url_path or not supabase_key_path:
        raise RuntimeError("Missing SUPABASE_URL_SSM_PATH or SUPABASE_KEY_SSM_PATH")

    supabase_url = get_ssm_param(supabase_url_path)
    supabase_key = get_ssm_param(supabase_key_path)
    supabase_client = create_client(supabase_url, supabase_key)

    # S3 input
    bucket = event.get("s3_bucket")
    key = event.get("s3_key")
    if not bucket or not key:
        raise ValueError("Missing s3_bucket or s3_key in event")

    data = read_s3_json(bucket, key)
    jobs = data.get("jobs", [])
    if not isinstance(jobs, list) or not jobs:
        return {"written": 0}

    rows = [map_row(j) for j in jobs if isinstance(j, dict) and j.get("_id")]
    if not rows:
        return {"written": 0}

    # Single upsert (no batching)
    supabase_client.table(TABLE_NAME).upsert(rows, on_conflict="hirebase_job_id").execute()

    return {"written": len(rows)}
