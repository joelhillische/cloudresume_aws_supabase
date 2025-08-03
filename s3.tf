resource "aws_s3_bucket" "job_input" {
  bucket        = "${module.labels.id}-input-files"
  force_destroy = true

  tags = module.labels.tags
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "${module.labels.id}-trigger-step-function"
  action        = "lambda:InvokeFunction"
  function_name = module.s3_trigger_lambda.lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.job_input.arn
}

resource "aws_s3_bucket_notification" "s3_trigger" {
  bucket = aws_s3_bucket.job_input.id

  lambda_function {
    lambda_function_arn = module.s3_trigger_lambda.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
