import os, json, io, boto3
from supabase import create_client

s3 = boto3.client("s3")
ssm = boto3.client("ssm")

def get_ssm_param(path: str) -> str:
    """Fetch a parameter from AWS SSM Parameter Store."""
    resp = ssm.get_parameter(Name=path, WithDecryption=True)
    return resp["Parameter"]["Value"]

def read_s3_json(bucket: str, key: str):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read())

def map_row(j: dict) -> dict:
    row = {
        "hirebase_job_id": j.get("_id"),
        "company_name": j.get("company_name"),
        "job_title": j.get("job_title"),
        "description_html": j.get("description"),
        "locations": j.get("locations"),
        "salary_range": j.get("salary_range"),
        "raw": j
    }
    # Only include date_posted if present and looks like YYYY-MM-DD
    dp = j.get("date_posted")
    if isinstance(dp, str) and len(dp) == 10:
        row["date_posted"] = dp  # Postgres DATE will accept 'YYYY-MM-DD'
    return row

def lambda_handler(event, context):
    # Read SSM paths from environment
    supabase_url_path = os.environ.get("SUPABASE_URL_SSM_PATH")
    supabase_key_path = os.environ.get("SUPABASE_KEY_SSM_PATH")

    if not supabase_url_path or not supabase_key_path:
        raise RuntimeError("Missing SUPABASE_URL_SSM_PATH or SUPABASE_KEY_SSM_PATH in environment variables")

    # Fetch credentials from SSM
    supabase_url = get_ssm_param(supabase_url_path)
    supabase_key = get_ssm_param(supabase_key_path)

    # Create Supabase client
    supabase_client = create_client(supabase_url, supabase_key)

    bucket = event.get("s3_bucket")
    key = event.get("s3_key")
    if not bucket or not key:
        raise ValueError("Missing s3_bucket or s3_key in event")

    data = read_s3_json(bucket, key)
    jobs = data.get("jobs", [])
    if not jobs:
        return {"written": 0}

    rows = [map_row(j) for j in jobs if j.get("_id")]

    # Upsert keyed by hirebase_job_id
    supabase_client.table("hirebase_jobs").upsert(rows, on_conflict="hirebase_job_id").execute()

    return {"written": len(rows)}
