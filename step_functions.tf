module "job_step_function" {
  source  = "terraform-aws-modules/step-functions/aws"
  version = "~> 5.0.1"

  name     = "${module.labels.id}-job-processing"
  role_arn = aws_iam_role.step_function_role.arn

  definition = jsonencode({
    Comment = "Triggered by S3 upload to start job processing",
    StartAt = "LogInput",
    States = {
      LogInput = {
        Type   = "Pass",
        Result = "Started with S3 input",
        End    = true
      }
    }
  })

  tags = module.labels.tags
}
