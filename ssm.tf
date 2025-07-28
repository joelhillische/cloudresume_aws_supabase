resource "aws_ssm_parameter" "supabase_url" {
  name  = var.supabase_url_ssm_path
  type  = "String"
  value = "dummy"

  lifecycle {
    ignore_changes = [value]
  }

  tags = module.labels.tags
}

resource "aws_ssm_parameter" "supabase_key" {
  name  = var.supabase_key_ssm_path
  type  = "SecureString"
  value = "dummy"

  lifecycle {
    ignore_changes = [value]
  }

  tags = module.labels.tags
}

resource "aws_ssm_parameter" "hirebase_url" {
  name  = var.hirebase_url_path
  type  = "String"
  value = "dummy"

  lifecycle {
    ignore_changes = [value]
  }

  tags = module.labels.tags
}

resource "aws_ssm_parameter" "hirebase_key" {
  name  = var.hirebase_key_path
  type  = "SecureString"
  value = "dummy"

  lifecycle {
    ignore_changes = [value]
  }

  tags = module.labels.tags
}
