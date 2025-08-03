import json
import boto3

s3 = boto3.client("s3")

def read_s3_json(bucket, key):
    print(f"Reading from s3://{bucket}/{key}")
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        job_data = json.loads(content)
        print("✅ JSON content:")
        print(json.dumps(job_data, indent=2))
        return job_data
    except Exception as e:
        print(f"❌ Error reading S3 object: {str(e)}")
        raise
