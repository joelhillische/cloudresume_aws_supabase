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
    SUPABASE_URL_SSM_PATH = var.supabase_url_ssm_path
    SUPABASE_KEY_SSM_PATH = var.supabase_key_ssm_path
  }

  timeout = 300

  cloudwatch_logs_retention_in_days = 1

  tags = module.labels.tags
}
