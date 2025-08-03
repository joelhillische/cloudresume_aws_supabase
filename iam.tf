resource "aws_iam_role" "lambda_exec" {
  name = "${module.labels.id}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = module.labels.tags
}

resource "aws_iam_policy" "lambda_ssm_access" {
  name        = "${module.labels.id}-ssm-access"
  description = "Allows Lambda to access SSM params"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParameterHistory"
        ],
        Resource = [
          aws_ssm_parameter.supabase_url.arn,
          aws_ssm_parameter.supabase_key.arn,
          aws_ssm_parameter.hirebase_url.arn,
          aws_ssm_parameter.hirebase_key.arn
        ]
      }
    ]
  })

  tags = module.labels.tags
}

resource "aws_iam_policy" "lambda_start_step_function" {
  name        = "${module.labels.id}-start-step-function"
  description = "Allows Lambda to start Step Functions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "states:StartExecution"
        ],
        Resource = [
          module.job_step_function.state_machine_arn
        ]
      }
    ]
  })

  tags = module.labels.tags
}

resource "aws_iam_role" "step_function_role" {
  name = "${module.labels.id}-step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "states.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = module.labels.tags
}

resource "aws_iam_role_policy_attachment" "lambda_step_fn_access_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_start_step_function.arn
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_access_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_ssm_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
