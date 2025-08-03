module "job_step_function" {
  source  = "terraform-aws-modules/step-functions/aws"
  version = "~> 5.0.1"

  create_role = false

  use_existing_role = true

  name     = "${module.labels.id}-job-processing"
  role_arn = aws_iam_role.step_function_role.arn

  definition = jsonencode({
    Comment = "Triggered by S3 upload to start job processing",
    StartAt = "LogInputLambda",
    States = {
      LogInputLambda = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = module.log_input_lambda.lambda_function_arn,
          Payload = {
            "s3_bucket.$" = "$.s3_bucket",
            "s3_key.$"    = "$.s3_key"
          }
        },
        End = true
      }
    }
  })

  tags = module.labels.tags

  depends_on = [aws_iam_role.step_function_role]
}
