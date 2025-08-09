import os
import json
import boto3
from supabase import create_client

# ---- AWS clients (init once per container) ----
s3 = boto3.client("s3")   # not used here but kept for parity with your template
ssm = boto3.client("ssm")

# ---- Helpers: AWS ----
def get_ssm_param(path: str) -> str:
    resp = ssm.get_parameter(Name=path, WithDecryption=True)
    return resp["Parameter"]["Value"]

PAGE_SIZE = int(os.environ.get("USER_PAGE_SIZE", "1000"))

# ---- Main handler ----
def lambda_handler(event, context):
    # SSM creds
    supabase_url_path = os.environ.get("SUPABASE_URL_SSM_PATH")
    supabase_key_path = os.environ.get("SUPABASE_KEY_SSM_PATH")
    supabase_table = os.environ.get("SUPABASE_USER_TABLE")
    if not supabase_url_path or not supabase_key_path:
        raise RuntimeError("Missing SUPABASE_URL_SSM_PATH or SUPABASE_KEY_SSM_PATH")

    supabase_url = get_ssm_param(supabase_url_path)
    supabase_key = get_ssm_param(supabase_key_path)
    supabase_client = create_client(supabase_url, supabase_key)

    # Fetch user ids (first page; expand to pagination later if needed)
    resp = supabase_client.table(supabase_table) \
        .select("id") \
        .order("id", desc=False) \
        .limit(PAGE_SIZE) \
        .execute()

    user_ids = [row["id"] for row in (resp.data or [])]

    return {
        "status": "success",
        "user_ids": user_ids
    }
