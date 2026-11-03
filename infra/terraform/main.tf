# Starter only: provider + a container registry (ECR).
# Still to add: networking, RDS Postgres, ElastiCache Redis, Secrets Manager and App Runner.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project = "geoclock"
      Owner   = var.owner
    }
  }
}

resource "aws_ecr_repository" "api" {
  name                 = "geoclock-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # lets `terraform destroy` remove it even with images inside

  image_scanning_configuration {
    scan_on_push = true
  }
}
