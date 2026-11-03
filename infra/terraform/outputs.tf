output "ecr_repository_url" {
  description = "Push your Docker image here."
  value       = aws_ecr_repository.api.repository_url
}
