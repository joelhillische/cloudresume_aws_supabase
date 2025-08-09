module "job_step_function" {
  source  = "terraform-aws-modules/step-functions/aws"
  version = "~> 5.0.1"

  create_role       = false
  use_existing_role = true

  name     = "${module.labels.id}-job-processing"
  role_arn = aws_iam_role.step_function_role.arn

  definition = jsonencode({
    Comment = "Ingest jobs then evaluate categories/filters for all users",
    StartAt = "WriteJobsToSupabase",
    States = {
      WriteJobsToSupabase = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = module.write_jobs_to_supabase.lambda_function_arn,
          Payload = {
            "s3_bucket.$" = "$.s3_bucket",
            "s3_key.$"    = "$.s3_key"
          }
        },
        Next = "ListUsers"
      },
      ListUsers = {
        Type     = "Task",
        Resource = "arn:aws:states:::lambda:invoke",
        Parameters = {
          FunctionName = module.list_users.lambda_function_arn,
          Payload      = {}
        },
        ResultSelector = {
          "user_ids.$" = "$.Payload.user_ids"
        },
        ResultPath = "$.users",
        Next       = "MapUsers"
      },
      MapUsers = {
        Type           = "Map",
        ItemsPath      = "$.users.user_ids",
        MaxConcurrency = 50, # tune based on Supabase limits
        Parameters = {
          "user_id.$" = "$$.Map.Item.Value"
        },
        Iterator = {
          StartAt = "ProcessUser",
          States = {
            ProcessUser = {
              Type     = "Task",
              Resource = "arn:aws:states:::lambda:invoke",
              Parameters = {
                FunctionName = module.process_categories.lambda_function_arn,
                Payload = {
                  "user_id.$" = "$.user_id"
                }
              },
              End = true
            }
          }
        },
        End = true
      }
    }
  })

  tags = module.labels.tags
}
