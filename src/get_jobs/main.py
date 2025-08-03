import requests
import boto3
import logging
import os
from datetime import datetime, timezone
import json

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# AWS clients
ssm = boto3.client("ssm")
s3 = boto3.client("s3")

# Load environment variable
S3_BUCKET = os.environ["S3_BUCKET_NAME"]

# Helper to fetch secrets from SSM
def get_ssm_param(name, decrypt=True):
    return ssm.get_parameter(Name=name, WithDecryption=decrypt)['Parameter']['Value']

# Load secrets from SSM
HIREBASE_URL = get_ssm_param(os.environ["HIREBASE_URL_SSM_PATH"])
HIREBASE_KEY = get_ssm_param(os.environ["HIREBASE_KEY_SSM_PATH"])

def lambda_handler(event, context):
    try:
        # Prepare request payload
        payload = {
            "date_posted": "2025-07-23",
            "keywords": ["aws"],
            "limit": 5,
            "locations": [{"country": "United States"}]
        }
        

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": HIREBASE_KEY
        }

        # Make the API request
        response = requests.post(HIREBASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Create a timestamped S3 object key
        now = datetime.now(timezone.utc)
        key = f"{now.year}/{now.month:02}/{now.day:02}/{now.hour:02}.json"

        # Print the result and intended S3 key path
        print(f"Would save to: s3://{S3_BUCKET}/{key}")
        print("HIREBASE Response:")
        print(json.dumps(data, indent=2))

        # Optionally write to S3
        # s3.put_object(
        #     Bucket=S3_BUCKET,
        #     Key=key,
        #     Body=json.dumps(data),
        #     ContentType="application/json"
        # )

        return {"status": "success", "key": key}

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}
