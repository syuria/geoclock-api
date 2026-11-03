variable "region" {
  description = "AWS region. eu-west-2 is London."
  type        = string
  default     = "eu-west-2"
}

variable "owner" {
  description = "Your name, added as a tag to every resource."
  type        = string
}
