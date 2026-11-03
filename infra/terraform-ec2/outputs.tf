output "api_url" {
  description = "Wait 3-5 minutes after apply for the first boot to finish, then try <api_url>/health."
  value       = "http://${aws_instance.api.public_ip}:8000"
}

output "instance_id" {
  description = "Use with Session Manager: aws ssm start-session --target <instance_id>"
  value       = aws_instance.api.id
}
