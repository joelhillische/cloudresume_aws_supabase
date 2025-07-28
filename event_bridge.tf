locals {
  schedules = {
    "trigger_12am" = {
      cron = "cron(0 0 * * ? *)" # 12:00 AM Central
    },
    "trigger_12pm" = {
      cron = "cron(0 12 * * ? *)" # 12:00 PM Central
    }
  }
}

resource "aws_scheduler_schedule" "daily_triggers" {
  for_each   = local.schedules
  name       = "${module.labels.id}-${each.key}"
  group_name = "default"

  schedule_expression          = each.value.cron
  schedule_expression_timezone = "America/Chicago"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = module.get_jobs_lambda.lambda_function_arn
    role_arn = aws_iam_role.event_bridge_role.arn
    input    = jsonencode({ trigger = each.key }) # Optional input to the Lambda
  }

  description = "Triggers the Lambda function at ${each.key == "trigger_12am" ? "12:00 AM" : "12:00 PM"} CST/CDT"
}

resource "aws_iam_role" "event_bridge_role" {
  name = "${module.labels.id}-event-bridge"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "scheduler.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })

  tags = module.labels.tags
}

resource "aws_iam_role_policy" "allow_lambda_invoke" {
  name = "${module.labels.id}-event-bridge"
  role = aws_iam_role.event_bridge_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action   = "lambda:InvokeFunction",
      Effect   = "Allow",
      Resource = module.get_jobs_lambda.lambda_function_arn
    }]
  })
}
