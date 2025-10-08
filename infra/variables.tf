# ============================================================================
# AWS Infrastructure Variables
# ============================================================================
# This file defines all input variables for the Terraform configuration.
# Variables are organized by category and include sensible defaults where
# appropriate. Override these values using terraform.tfvars or -var flags.
# ============================================================================

# ============================================================================
# General Configuration
# ============================================================================

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "django-prompts"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# ============================================================================
# Networking Configuration
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use (minimum 2 for high availability)"
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2
    error_message = "At least 2 availability zones are required for high availability."
  }
}

# ============================================================================
# Application Configuration
# ============================================================================

variable "app_port" {
  description = "Port on which the Django application runs"
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health/"
}

variable "container_image" {
  description = "Docker image for the Django application (ECR URL)"
  type        = string
  default     = "django-prompts-app:latest"

  # Example: "<account-id>.dkr.ecr.us-east-1.amazonaws.com/django-prompts-app:latest"
}

# ============================================================================
# ECS Configuration
# ============================================================================

variable "ecs_task_cpu" {
  description = "CPU units for ECS task (1024 = 1 vCPU)"
  type        = string
  default     = "512"

  validation {
    condition     = contains(["256", "512", "1024", "2048", "4096"], var.ecs_task_cpu)
    error_message = "Valid values: 256, 512, 1024, 2048, 4096."
  }
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = string
  default     = "1024"

  validation {
    condition     = contains(["512", "1024", "2048", "4096", "8192"], var.ecs_task_memory)
    error_message = "Valid values: 512, 1024, 2048, 4096, 8192."
  }
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_count" {
  description = "Minimum number of ECS tasks for auto-scaling"
  type        = number
  default     = 2
}

variable "ecs_max_count" {
  description = "Maximum number of ECS tasks for auto-scaling"
  type        = number
  default     = 10
}

# ============================================================================
# Database Configuration
# ============================================================================

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "prompts_db"
}

variable "db_username" {
  description = "PostgreSQL database username"
  type        = string
  default     = "django_user"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL database password (use AWS Secrets Manager in production)"
  type        = string
  sensitive   = true
  default     = "change-me-in-production"

  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters."
  }
}

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.3"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20
    error_message = "Allocated storage must be at least 20 GB."
  }
}

# ============================================================================
# Monitoring and Logging
# ============================================================================

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Invalid log retention period."
  }
}

# ============================================================================
# SSL/TLS Configuration (Optional)
# ============================================================================

variable "ssl_certificate_arn" {
  description = "ARN of ACM SSL certificate for HTTPS (optional)"
  type        = string
  default     = ""
}

# ============================================================================
# Tags
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

