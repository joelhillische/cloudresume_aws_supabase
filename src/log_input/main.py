import json
import boto3

s3 = boto3.client("s3")

from s3_reader import read_s3_json

def lambda_handler(event, context):
    bucket = event.get("s3_bucket")
    key = event.get("s3_key")

    try:
        job_data = read_s3_json(bucket, key)

        return {
            "status": "success",
            "bucket": bucket,
            "key": key,
            "data": job_data  # optional: include parsed JSON in the response
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
