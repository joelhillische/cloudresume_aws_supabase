import json
import os
import boto3

# Get Step Function ARN from environment variable
STEP_FUNCTION_ARN = os.environ["STEP_FUNCTION_ARN"]

# Create client for Step Functions
sfn_client = boto3.client("stepfunctions")


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        input_payload = {
            "s3_bucket": bucket,
            "s3_key": key
        }

        response = sfn_client.start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            input=json.dumps(input_payload)
        )

        print("Step Function started:", response["executionArn"])

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Step Function started", "executionArn": response["executionArn"]})
        }

    except Exception as e:
        print("Error starting Step Function:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
