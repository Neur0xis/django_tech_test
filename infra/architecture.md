# System Architecture

This diagram shows the AWS infrastructure for the Django application with WebSocket support.

```mermaid
graph TD
    %% Entry point
    A[Client / Browser] -->|HTTP / WebSocket| B[Application Load Balancer]

    %% Core compute
    B --> C["ECS Fargate Task<br/>(Django + DRF + Channels)"]
    
    %% Persistence
    C --> D[(RDS PostgreSQL)]
    
    %% Secrets and config
    C --> E[(AWS Secrets Manager)]
    
    %% Logs and monitoring
    C --> F[(CloudWatch Logs)]
    
    %% Container registry
    C --> G[(ECR Repository)]
    
    %% Optional section
    subgraph Optional Future Integrations
        H[(Redis Channel Layer)]:::optional
        I[(S3 Bucket for Static/Media Files)]:::optional
    end
    C -.-> H
    C -.-> I

    classDef optional fill:#e0e0e0,stroke:#999,stroke-width:1px,font-style:italic;
```

## Components

- **Client/Browser**: End users accessing the application
- **Application Load Balancer**: Routes HTTP and WebSocket traffic
- **ECS Fargate**: Containerized Django application with Django REST Framework and Channels
- **RDS PostgreSQL**: Primary database
- **AWS Secrets Manager**: Secure credential storage
- **CloudWatch Logs**: Centralized logging
- **ECR Repository**: Docker image storage

## Optional Components

- **Redis Channel Layer**: For scaling WebSocket connections across multiple containers
- **S3 Bucket**: For static and media file storage
