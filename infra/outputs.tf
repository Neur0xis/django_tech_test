# ============================================================================
# AWS Infrastructure Outputs
# ============================================================================
# This file defines outputs that are useful for connecting to the deployed
# infrastructure, debugging, and integrating with other systems.
# ============================================================================

# ============================================================================
# Application Access
# ============================================================================

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer (use this to access the application)"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the ALB (for Route53 alias records)"
  value       = aws_lb.main.zone_id
}

output "application_url" {
  description = "Full URL to access the application"
  value       = "http://${aws_lb.main.dns_name}"
}

output "websocket_url" {
  description = "WebSocket URL for real-time connections"
  value       = "ws://${aws_lb.main.dns_name}/ws/prompts/"
}

# ============================================================================
# Database Connection
# ============================================================================

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS PostgreSQL host address"
  value       = aws_db_instance.postgres.address
  sensitive   = true
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
}

# ============================================================================
# ECS Cluster Information
# ============================================================================

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = aws_ecs_task_definition.app.arn
}

# ============================================================================
# Networking Information
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ips" {
  description = "Public IP addresses of NAT gateways"
  value       = aws_eip.nat[*].public_ip
}

# ============================================================================
# Security Groups
# ============================================================================

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS tasks security group"
  value       = aws_security_group.ecs_tasks.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

# ============================================================================
# IAM Roles
# ============================================================================

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

# ============================================================================
# CloudWatch Logs
# ============================================================================

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for ECS"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs.arn
}

# ============================================================================
# ECR Repository
# ============================================================================

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_repository_name" {
  description = "Name of the ECR repository"
  value       = aws_ecr_repository.app.name
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.app.arn
}

# ============================================================================
# Environment Information
# ============================================================================

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

# ============================================================================
# Connection String Examples (for documentation)
# ============================================================================

output "database_connection_example" {
  description = "Example database connection string (replace password)"
  value       = "postgresql://${var.db_username}:PASSWORD@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

# ============================================================================
# Deployment Commands (for documentation)
# ============================================================================

output "ecs_update_command" {
  description = "AWS CLI command to force new ECS deployment"
  value       = "aws ecs update-service --cluster ${aws_ecs_cluster.main.name} --service ${aws_ecs_service.app.name} --force-new-deployment --region ${var.aws_region}"
}

output "ecs_scale_command" {
  description = "AWS CLI command to scale ECS service"
  value       = "aws ecs update-service --cluster ${aws_ecs_cluster.main.name} --service ${aws_ecs_service.app.name} --desired-count <COUNT> --region ${var.aws_region}"
}

output "logs_command" {
  description = "AWS CLI command to view application logs"
  value       = "aws logs tail ${aws_cloudwatch_log_group.ecs.name} --follow --region ${var.aws_region}"
}

