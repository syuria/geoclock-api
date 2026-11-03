# One-day deployment: a single EC2 server running the project's docker compose
# (Flask API + Postgres + Redis). Simple and cheap; a production setup would use managed
# Postgres (RDS) and Redis (ElastiCache) in private subnets, behind HTTPS.
#
#   terraform init
#   terraform apply -var owner=syuria -var repo_url=https://github.com/syuria/geoclock-api.git -var my_ip=$(curl -s https://checkip.amazonaws.com)/32
#   terraform destroy  (when you finish)

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

# ---- Look-ups (data sources read existing things; they create nothing) ----

# The default VPC and its subnets exist in every AWS account.
data "aws_vpc" "default" {
  default = true
}

# Latest Ubuntu 24.04 image published by Canonical (owner ID 099720109477).
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

# ---- Firewall --------------------------------------------------------------

# Only port 8000 (the API) is open, and only to your own IP address.
# Postgres (5432) and Redis (6379) are not reachable from the internet.
resource "aws_security_group" "api" {
  name        = "geoclock-api"
  description = "GeoClock API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "API from my IP"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    description = "Outbound for package installs and git clone"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---- Access without SSH keys -------------------------------------------------

# Lets you open a shell from the AWS console (Systems Manager Session Manager),
# so no SSH port or key pair is needed. Least privilege: only the SSM policy.
resource "aws_iam_role" "ec2" {
  name = "geoclock-ec2"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "geoclock-ec2"
  role = aws_iam_role.ec2.name
}

# ---- The server ---------------------------------------------------------------

resource "aws_instance" "api" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.api.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  # Runs once on first boot: installs Docker, clones the repo, starts the stack.
  user_data = templatefile("${path.module}/user_data.sh", {
    repo_url = var.repo_url
  })
  user_data_replace_on_change = true

  # Require IMDSv2 tokens for the instance metadata service (blocks a common
  # credential-theft route).
  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "geoclock-api"
  }
}
