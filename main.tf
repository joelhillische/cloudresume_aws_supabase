terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = var.region
}

module "labels" {
  source  = "cloudposse/label/null"
  version = "~> 0.25.0"

  namespace = "cloudresume-aws-supabase"
  stage     = var.stage

  tags = {
    "Managed By" = "terraform"
  }
}
