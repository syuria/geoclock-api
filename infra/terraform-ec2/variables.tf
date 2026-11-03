variable "region" {
  description = "AWS region. eu-west-2 is London."
  type        = string
  default     = "eu-west-2"
}

variable "owner" {
  description = "Your name, added as a tag to every resource."
  type        = string
}

variable "repo_url" {
  description = "Public HTTPS URL of your GitHub repo, e.g. https://github.com/syuria/geoclock-api.git"
  type        = string
}

variable "my_ip" {
  description = "Your public IP in CIDR form, e.g. 203.0.113.10/32. Only this address can reach the API."
  type        = string
}

variable "instance_type" {
  description = "t3.small has 2 GB RAM, enough for the API, Postgres and Redis together."
  type        = string
  default     = "t3.small"
}
