variable "region" {
  type    = string
  default = "us-east-2"
}

variable "stage" {
  type    = string
  default = "sandbox"
}

variable "supabase_url_ssm_path" {
  type    = string
  default = "/cloudresume-aws/supabase/url"
}

variable "supabase_key_ssm_path" {
  type    = string
  default = "/cloudresume-aws/supabase/key"
}

variable "hirebase_key_path" {
  type    = string
  default = "/hirebase/key"
}

variable "hirebase_url_path" {
  type    = string
  default = "/hirebase/url"
}
