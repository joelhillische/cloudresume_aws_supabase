resource "aws_lambda_layer_version" "all_libraries_layer" {
  layer_name          = "${module.labels.id}-layer"
  compatible_runtimes = ["python3.11"]
  filename            = "${path.module}/layer/layer.zip" # Local path to ZIP file
  source_code_hash    = filebase64sha256("${path.module}/layer/layer.zip")
}
