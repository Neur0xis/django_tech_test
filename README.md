## ⚠️ Disclaimer

This project was built as part of a technical assessment.  
It demonstrates architecture design, clean code practices, and API structure using Django and DRF.  
**This setup is not representative of a production deployment.**

> **Note:** The AWS deployment plan and Terraform files are conceptual examples created only for demonstration purposes. Redis/ElastiCache, advanced scaling strategies, comprehensive monitoring configurations, and CI/CD pipelines are included to show architectural understanding but are **not deployed or required** for this assessment. This project focuses on backend implementation and clean code architecture.

> **AI Simulation:** All AI responses are generated using a simulated language model, not a real LLM (e.g., OpenAI or HuggingFace).  
> The logic in `app_prompts/services.py` emulates deterministic embeddings and responses for demonstration purposes only.

---

## Project Overview

This is a Django REST Framework application that provides:
- **AI Prompt Processing**: Accepts prompts, processes them using a language model, and stores responses
- **Semantic Search**: Returns similar prompts using FAISS vector similarity search
- **Real-time Communication**: WebSocket support for streaming responses
- **Authentication**: Token-based JWT authentication
- **Rate Limiting**: API throttling (1 req/sec, 10 req/min)

**Tech Stack**: Django 5.2, DRF, Channels, PostgreSQL, FAISS, Docker

---

## Environment Configuration

This project uses a modular settings structure with three configuration files:

- **`app/settings/base.py`**: Shared settings for all environments (database config, installed apps, middleware)
- **`app/settings/dev.py`**: Development settings (`DEBUG=True`, open CORS, local database)
- **`app/settings/prod.py`**: Production settings (`DEBUG=False`, restricted CORS, secure cookies)

### Switching Environments

Use the `DJANGO_SETTINGS_MODULE` environment variable to select the configuration:

**Development:**
```bash
# macOS/Linux
export DJANGO_SETTINGS_MODULE=app.settings.dev

# Windows (PowerShell)
$env:DJANGO_SETTINGS_MODULE="app.settings.dev"
```

**Production (default in Docker):**
```bash
# macOS/Linux
export DJANGO_SETTINGS_MODULE=app.settings.prod

# Windows (PowerShell)
$env:DJANGO_SETTINGS_MODULE="app.settings.prod"
```

> **Note:** When running with Docker, production settings are used by default as configured in the Dockerfile.

### Security Note

> **Security Note:**  
> The `SECRET_KEY` used by Django is loaded from an environment variable.  
> During development, define it in your `.env` file.  
> In production or CI/CD, it should be injected securely via secrets (e.g., AWS Secrets Manager or GitHub Secrets).  
> This prevents accidental exposure of sensitive keys in source control.

> **Environment Override:**  
> In containerized or CI/CD environments, environment variables defined externally  
> (for example in ECS Task Definitions, GitHub Actions, or Docker Compose files)  
> override defaults set in the Dockerfile or within the code.  
> This allows the same Docker image to be reused safely across development, testing, and production environments.

---

## Local Development

### Prerequisites
- Docker and Docker Compose installed

### Running with Docker Compose

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd django_tech_test
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your local database credentials
   ```

3. **Generate SECRET_KEY**
   
   Django requires a `SECRET_KEY` for cryptographic signing and user management. The SECRET_KEY must be generated before building the Docker image as Django loads it at build time.
   
   **Generate a new key:**
   ```bash
   docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
   
   Or use this simpler method:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
   
   Copy the generated value and add it to your `.env` file:
   ```
   SECRET_KEY=your-generated-secret-key
   ```
   
   > This key must remain secret. It is required for running migrations, creating users, managing sessions, and securing Django's cryptographic features.

4. **Start the services**
   ```bash
   docker-compose up --build
   ```
   
   > **Note:** Docker runs with production settings by default (`app.settings.prod`), as defined in the Dockerfile with `ENV DJANGO_SETTINGS_MODULE`.

5. **Run migrations** (first time only)
   ```bash
   docker-compose exec web python manage.py migrate
   ```

6. **Create a superuser** (optional)
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

7. **Access the application**
   - API: http://localhost:8000
   - WebSocket: ws://localhost:8000/ws/prompts/<username>/
   
   **Example:**
   - `ws://localhost:8000/ws/prompts/alice/`
   
   > If the `<username>` parameter is missing, the connection will be closed gracefully with a JSON error message instead of a server error.
   > 
   > Example response:
   > ```json
   > {"error": "Missing 'username' parameter. Use ws://host/ws/prompts/<username>/"}
   > ```

---

## WebSocket Usage and Flow

The WebSocket endpoint acts as an optional real-time channel for receiving prompt responses.
It integrates directly with the `POST /prompts` endpoint when the request body includes `"websocket": true`.

### Workflow

1. Open a WebSocket connection using your chosen identifier:
   ```
   ws://localhost:8000/ws/prompts/<username>/
   ```
   Example:
   ```
   ws://localhost:8000/ws/prompts/neur0x/
   ```

2. Send a new prompt via:
   ```
   POST /prompts
   ```
   with the following body:
   ```json
   {
     "prompt_text": "Explain the speed of light.",
     "websocket": true
   }
   ```
   The backend generates the response and pushes it through the WebSocket channel
   corresponding to the specified `<username>`.

3. The connected WebSocket receives a message like:
   ```json
   {
     "response_text": "The speed of light is approximately 299,792 kilometers per second..."
   }
   ```

4. If the `<username>` parameter is missing in the connection URL, the server responds gracefully:
   ```json
   {
     "error": "Missing 'username' parameter. Use ws://host/ws/prompts/<username>/"
   }
   ```
   and closes the connection with code 4000, avoiding a server error.

### Purpose of the WebSocket Room

Each WebSocket connection creates a logical communication channel (a *room*) based on the `<username>` value.
This room acts as an isolated group where messages are sent specifically to that client.

For this technical assessment:
- The `<username>` does **not** need to correspond to a registered user.
- Any name can be used to open a dedicated channel.
- Responses sent from `/prompts` with `"websocket": true` are routed to the matching room (`prompts_<username>`).

> **Note:**  
> This setup demonstrates the requested WebSocket integration from the assessment.  
> In a production environment, these rooms could be tied to authenticated users (via JWT)
> to ensure that only the rightful user receives their own prompt responses.

### WebSocket Influence

The WebSocket channel does **not** modify or trigger REST endpoints.
It functions as a passive, real-time delivery mechanism:
- REST endpoints (such as `POST /prompts`) handle all application logic, validation, and database updates.
- The WebSocket only receives responses or notifications pushed from the backend.
- No data is created, updated, or deleted through the WebSocket connection.

This design follows the assessment's requirement:
the WebSocket serves as an *optional output channel* for `/prompts`,
not as a replacement for REST API interactions.

### Message Handling

The WebSocket endpoint expects messages in JSON format with a `type` field.

**Expected Message Format:**
```json
{
  "type": "ping"
}
```

**Supported Message Types:**

1. **Ping/Pong (Connectivity Testing):**
   
   Send:
   ```json
   {
     "type": "ping"
   }
   ```
   
   Receive:
   ```json
   {
     "type": "pong",
     "timestamp": "2025-10-08T12:34:56.789Z"
   }
   ```

2. **Echo (General Testing):**
   
   Send any message with a `type` field (other than "ping"):
   ```json
   {
     "type": "test",
     "data": "hello"
   }
   ```
   
   Receive:
   ```json
   {
     "type": "echo",
     "data": {
       "type": "test",
       "data": "hello"
     },
     "timestamp": "2025-10-08T12:34:56.789Z"
   }
   ```

**Error Handling:**

- **Invalid JSON:** If the message is not valid JSON, the server responds with:
  ```json
  {
    "type": "error",
    "message": "Invalid JSON format",
    "timestamp": "2025-10-08T12:34:56.789Z"
  }
  ```

- **Missing 'type' Field:** If the message is valid JSON but lacks a `type` field:
  ```json
  {
    "type": "error",
    "message": "Missing 'type' field",
    "timestamp": "2025-10-08T12:34:56.789Z"
  }
  ```

- **Empty Messages:** Empty or whitespace-only messages are silently ignored.

**Note:** These message types are for testing the WebSocket connection. The primary purpose of the WebSocket is to receive real-time prompt responses pushed from the backend when using `POST /prompts` with `"websocket": true`.

---

## API Usage Examples

### 1. POST /login/ - Obtain JWT Token

Authenticate and receive JWT tokens for accessing protected endpoints.

**Request:**
```bash
curl -X POST http://localhost:8000/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "yourpassword"
  }'
```

**Request Body:**
```json
{
  "username": "alice",
  "password": "yourpassword"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Use the `access` token in the `Authorization` header for subsequent requests: `Authorization: Bearer <access_token>`

---

### 2. POST /prompts/ - Create a Prompt

Submit a prompt to generate an AI response with semantic embeddings.

**Headers Required:**
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request:**
```bash
curl -X POST http://localhost:8000/prompts/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_text": "What are the benefits of using Django REST Framework?",
    "websocket": false
  }'
```

**Request Body:**
```json
{
  "prompt_text": "What are the benefits of using Django REST Framework?",
  "websocket": false
}
```

**Parameters:**
- `prompt_text` (string, required): The prompt text to process
- `websocket` (boolean, optional, default: false): Set to `true` to receive the response via WebSocket in addition to HTTP response

**Response (201 CREATED):**
```json
{
  "id": 1,
  "user": "alice",
  "prompt_text": "What are the benefits of using Django REST Framework?",
  "response_text": "Django REST Framework (DRF) provides several key benefits: 1) Powerful serialization for converting complex data types, 2) Built-in authentication and permissions, 3) Browsable API for easy testing, 4) Comprehensive documentation, and 5) Strong community support.",
  "created_at": "2025-10-08T12:34:56.789Z"
}
```

> **Note:**  
> The `embedding` field is stored internally for FAISS semantic search but is **not included**  
> in API or WebSocket responses. Only `id`, `user`, `prompt_text`, `response_text`,  
> and `created_at` are returned to clients.

**Rate Limiting:** This endpoint is rate-limited to 1 request per second and 10 requests per minute per user.

---

### 3. GET /prompts/similar - Find Similar Prompts

Perform semantic search to find prompts similar to your query using FAISS vector similarity.

**Headers Required:**
- `Authorization: Bearer <access_token>`

**Request:**
```bash
curl -X GET "http://localhost:8000/prompts/similar?prompt=Tell%20me%20about%20Django" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Query Parameters:**
- `prompt` (string, required): The query text to find similar prompts

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": "alice",
    "prompt_text": "What are the benefits of using Django REST Framework?",
    "response_text": "Django REST Framework (DRF) provides several key benefits...",
    "similarity_score": 0.234,
    "created_at": "2025-10-08T12:34:56.789Z"
  },
  {
    "id": 3,
    "user": "alice",
    "prompt_text": "How do I set up Django with PostgreSQL?",
    "response_text": "To set up Django with PostgreSQL, you need to...",
    "similarity_score": 0.456,
    "created_at": "2025-10-08T13:22:11.123Z"
  }
]
```

**Notes:**
- Returns up to 5 most similar prompts
- Lower `similarity_score` values indicate higher similarity
- Only returns prompts belonging to the authenticated user

---

### Authentication Note

All API endpoints except `/login/` require JWT authentication. Include the access token in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

If the token expires, use the `/auth/refresh/` endpoint with your refresh token to obtain a new access token.

---

### Stop the services
```bash
docker-compose down
```

---

## Testing

This project includes comprehensive unit tests covering authentication, API endpoints, WebSocket functionality, rate limiting, and semantic search.

### Running Tests

**Run all tests:**
```bash
docker-compose exec web pytest
```

**Run specific test files:**
```bash
docker-compose exec web pytest app_prompts/tests/test_prompts.py
docker-compose exec web pytest app_prompts/tests/test_services.py
```

### Test Coverage

Tests are located in `app_prompts/tests/` and cover:

- **JWT Authentication** (`test_prompts.py`)
  - Login endpoint token generation
  - Invalid credential handling
  
- **Prompt Endpoints** (`test_prompts.py`)
  - Protected endpoint access
  - Prompt creation and response generation
  - User isolation (users can only access their own prompts)
  - Rate limiting (1 req/sec, 10 req/min)
  
- **Semantic Search** (`test_prompts.py`)
  - FAISS similarity search
  - Query parameter validation
  
- **AI Services** (`test_services.py`)
  - Embedding generation
  - Response generation
  - FAISS index operations

### Test Configuration

Test settings are configured in `pytest.ini` to use development settings (`app.settings.dev`) with an in-memory SQLite database for fast test execution.

---

## Continuous Integration (CI/CD)

This repository includes a GitHub Actions workflow for automated testing and deployment as an **optional bonus** from the technical assessment.

### Workflow Configuration

**Location:** `.github/workflows/ci.yml`

The workflow consists of two jobs that run automatically on every push and pull request to the `main` branch:

#### 1. Test Job
Runs on all pushes and pull requests to validate code integrity:
- Sets up Python 3.12
- Starts a PostgreSQL 15 service container
- Installs dependencies from `requirements.txt`
- Runs Django migrations
- Executes the full test suite with `pytest`

**Note:** The test job uses simple dummy values and doesn't require any secrets.

#### 2. Deploy Job
Runs only on pushes to `main` (after tests pass):
- Configures AWS credentials
- Logs into Amazon ECR (Elastic Container Registry)
- Builds the Docker image
- Tags the image with git SHA and `latest`
- Pushes the image to ECR

### Technology Stack

- **CI Platform:** GitHub Actions
- **Python Version:** 3.12
- **Database:** PostgreSQL 15 (with health checks)
- **Test Framework:** pytest with pytest-django
- **Container Registry:** AWS ECR
- **Configuration:** Uses `app.settings.dev` for testing

### Required GitHub Secrets

To enable ECR deployment, configure the following secrets in your GitHub repository settings:

```
AWS_ACCESS_KEY_ID          # AWS IAM access key
AWS_SECRET_ACCESS_KEY      # AWS IAM secret key
AWS_REGION                 # AWS region (e.g., us-east-1)
ECR_REPOSITORY_NAME        # ECR repository name (e.g., django-prompts-dev)
```

**Setting up secrets:**
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with its corresponding value

**IAM Permissions Required:**
The AWS credentials need the following permissions:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`

### Purpose

The workflow provides:
- **Continuous Integration:** Automated testing on every code change
- **Continuous Deployment:** Automatic Docker image builds and ECR uploads
- **Quality Gates:** Tests must pass before deployment
- **Version Control:** Each image is tagged with the git commit SHA

**Note:** This pipeline builds and pushes Docker images to ECR but does not automatically deploy to ECS. The simulated AI services (`app_prompts/services.py`) are sufficient for CI validation without requiring external API keys or compute resources.

---

## Deployment Plan (AWS)

This section outlines a conceptual deployment strategy for AWS, demonstrating understanding of cloud architecture for this technical assessment.

### Architecture Overview

See the full diagram in [`infra/architecture.md`](./infra/architecture.md).

### Key Components

**1. Application Load Balancer (ALB)**
- Routes HTTP/HTTPS traffic to ECS tasks
- Handles WebSocket upgrade requests for Django Channels
- Provides SSL/TLS termination using AWS Certificate Manager

**2. ECS Fargate**
- Serverless container orchestration for running Django application
- Runs with Daphne ASGI server for WebSocket support
- Eliminates server management overhead

**3. RDS PostgreSQL**
- Managed database service with automatic backups and patching
- Multi-AZ deployment for high availability
- Stores prompts, responses, and user data

**4. AWS Secrets Manager**
- Secure storage for sensitive configuration (database credentials, Django secret key, JWT secrets)
- Integrates with ECS task definitions for runtime secret injection

**5. CloudWatch**
- Centralized logging for application and container logs
- Monitoring for metrics like CPU, memory, request rates, and error rates
- Alarms for operational issues

**6. ECR (Elastic Container Registry)**
- Private repository for Docker images
- Images are built locally or via CI/CD and pushed to ECR for deployment

**7. AI Processing Layer (Simulated)**
- **Embeddings**: Deterministic 384-dimensional vectors generated using SHA256 hashing (`get_embedding()` in `services.py`)
- **Responses**: Pattern-matched simulated responses (`generate_response()` in `services.py`)
- **FAISS**: In-memory vector similarity search for semantic matching
- **Purpose**: Demonstrates AI workflow without requiring external LLM API keys or compute resources
- **Production Note**: Replace with actual embedding models (e.g., sentence-transformers) and LLM APIs (OpenAI, Anthropic, etc.)

### WebSocket Channel Layer

For local development, Django Channels uses an **in-memory channel layer**. For production on AWS, you would configure:
- **ElastiCache Redis**: As a shared channel layer for multi-container WebSocket communication
- **Alternative**: Run Redis as a separate ECS service for cost-effective testing

---

## Infrastructure as Code

The `infra/` directory contains architecture documentation and Terraform configuration skeleton demonstrating infrastructure provisioning:

```
infra/
├── architecture.md  # System architecture diagram and component descriptions
├── main.tf          # Core AWS resources (VPC, ECS, RDS, ALB, security groups)
├── variables.tf     # Configurable parameters (region, instance sizes, etc.)
└── outputs.tf       # Useful outputs (ALB DNS, RDS endpoint, etc.)
```

**Key Terraform Resources Defined:**
- VPC with public/private subnets across multiple availability zones
- Security groups following least-privilege principles
- ECS cluster, task definitions, and service configurations
- RDS PostgreSQL instance with Multi-AZ support
- Application Load Balancer with target groups
- CloudWatch log groups for centralized logging
- IAM roles and policies for ECS task execution

**Note:** This is a conceptual skeleton for demonstration. To deploy, you would need to:
1. Configure AWS credentials and backend state storage
2. Customize variables in `terraform.tfvars`
3. Run `terraform init`, `terraform plan`, and `terraform apply`
4. Build and push Docker images to ECR
5. Update ECS services to use the new task definitions

---

## Repository Structure

```
django_tech_test/
├── app/                      # Django project configuration
│   ├── settings/             # Environment-specific settings (base, dev, prod)
│   ├── routing.py            # WebSocket routing
│   ├── middleware.py         # Custom middleware
│   └── urls.py               # URL routing
├── app_prompts/              # Main application
│   ├── models.py             # Prompt model with vector embeddings
│   ├── views.py              # REST API endpoints
│   ├── consumers.py          # WebSocket consumers
│   ├── services.py           # Business logic (FAISS, LLM integration)
│   ├── serializers.py        # DRF serializers
│   └── tests/                # Unit tests
│       ├── test_prompts.py   # API and authentication tests
│       └── test_services.py  # Service layer tests
├── infra/                    # Terraform configuration (conceptual)
│   ├── architecture.md       # Architecture diagram and descriptions
│   ├── main.tf               # Core AWS resources
│   ├── variables.tf          # Configuration parameters
│   └── outputs.tf            # Terraform outputs
├── Dockerfile                # Container definition
├── .dockerignore             # Docker build exclusions
├── docker-compose.yml        # Local development setup
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
├── pytest.ini                # Test configuration
├── challenge.md              # Original technical assessment requirements
└── README.md                 # This file
```

---

## Summary

This project demonstrates a well-architected Django REST API with real-time WebSocket capabilities, semantic search using FAISS, and JWT authentication. The included AWS deployment plan and Terraform configuration showcase understanding of cloud infrastructure, containerization, and production deployment considerations for the technical assessment.
