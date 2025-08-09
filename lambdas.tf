module "s3_trigger_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name   = "${module.labels.id}-s3-trigger"
  handler         = "main.lambda_handler"
  runtime         = "python3.11"
  build_in_docker = true

  source_path = "${path.root}/src/s3_trigger"

  architectures = ["x86_64"]

  # Reuse shared role and layer
  create_role = false
  lambda_role = aws_iam_role.lambda_exec.arn

  layers = [
    aws_lambda_layer_version.all_libraries_layer.arn
  ]

  environment_variables = {
    STEP_FUNCTION_ARN = module.job_step_function.state_machine_arn
  }

  timeout                           = 60
  cloudwatch_logs_retention_in_days = 3

  tags = module.labels.tags
}

# Gets the jobs and writes them to an object in an s3 bucket
module "get_jobs_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name = "${module.labels.id}-get-jobs"
  handler       = "main.lambda_handler"

  runtime = "python3.11"

  build_in_docker = true

  source_path = "${path.root}/src/get_jobs"

  architectures = ["x86_64"]

  create_role = false
  lambda_role = aws_iam_role.lambda_exec.arn

  layers = [
    aws_lambda_layer_version.all_libraries_layer.arn
  ]

  environment_variables = {
    HIREBASE_URL_SSM_PATH = var.hirebase_url_path
    HIREBASE_KEY_SSM_PATH = var.hirebase_key_path
    S3_BUCKET_NAME        = aws_s3_bucket.job_input.id
  }

  timeout = 300

  cloudwatch_logs_retention_in_days = 1

  tags = module.labels.tags
}

# Takes the s3 bucket and object and writes the jobs to Supabase 
module "write_jobs_to_supabase" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name   = "${module.labels.id}-jobs-to-supabase"
  handler         = "main.lambda_handler"
  runtime         = "python3.11"
  build_in_docker = true
  source_path     = "${path.root}/src/write_jobs_to_supabase"

  create_role = false
  lambda_role = aws_iam_role.lambda_exec.arn

  timeout                           = 30
  cloudwatch_logs_retention_in_days = 1

  environment_variables = {
    SUPABASE_TABLE        = "hirebase_jobs"
    SUPABASE_URL_SSM_PATH = var.supabase_url_ssm_path
    SUPABASE_KEY_SSM_PATH = var.supabase_key_ssm_path
    S3_BUCKET_NAME        = aws_s3_bucket.job_input.id
  }

  layers = [
    aws_lambda_layer_version.all_libraries_layer.arn
  ]

  tags = module.labels.tags
}
