# odoo-api-connector

[![CI](https://github.com/SBillion/odoo-api-connector/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SBillion/odoo-api-connector/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/SBillion/odoo-api-connector/branch/main/graph/badge.svg)](https://codecov.io/gh/SBillion/odoo-api-connector)
[![Python](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/downloads/)

A FastAPI connector to interact with Odoo API

## Features

- FastAPI application with `/contacts` and `/contacts/{contact_id}` endpoints
- Odoo API client with authentication
- Full type hints support
- Unit and functional tests
- Test coverage reporting
- Linting with Ruff
- Docker support with docker-compose

## Requirements

- Python 3.14+
- UV package manager
- Docker and Docker Compose (for containerized setup)

## Installation

### Local Development

1. Install UV (if not already installed):
```bash
pip install uv
```

2. Install dependencies:
```bash
uv sync
```

3. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

4. Update the `.env` file with your Odoo credentials.

## Running the Application

### Using FastAPI CLI (Development)

```bash
uv run fastapi dev app.main:app
```

The API will be available at `http://localhost:8000`

API documentation is automatically available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Alternative: Using UV with Uvicorn

```bash
uv run uvicorn app.main:app --reload
```

### Using Docker Compose

```bash
docker-compose up -d
```

This will start:
- Odoo server on `http://localhost:8069`
- PostgreSQL database
- FastAPI application on `http://localhost:8000`

## API Endpoints

### Documentation Endpoints

Interactive API documentation is automatically generated:

- **GET /docs** - Swagger UI for interacting with the API
- **GET /redoc** - ReDoc (alternative API documentation)
- **GET /openapi.json** - OpenAPI schema in JSON format

### Business Endpoints

### GET /
Root endpoint returning a welcome message.

### GET /contacts
Get list of contacts from Odoo API.

Returns a list of contact objects with fields: `id`, `name`, `email`, `phone`, `company_name`.

**Example:**
```bash
curl http://localhost:8000/contacts
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "123456789",
    "company_name": "Acme Corp"
  },
  {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "987654321",
    "company_name": "Tech Co"
  }
]
```

### GET /contacts/{contact_id}
Get a specific contact by ID from Odoo API.

**Parameters:**
- `contact_id` (path parameter): The ID of the contact to retrieve

**Example:**
```bash
curl http://localhost:8000/contacts/1
```

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "123456789",
  "company_name": "Acme Corp"
}
```

**Error Response (404):**
```json
{
  "detail": "Contact with ID 999 not found"
}
```

## Development

### Pre-commit Hooks

This project uses `pre-commit` to automatically check code quality before commits.

Install the pre-commit hooks:
```bash
uv run pre-commit install
```

Hooks will run automatically on `git commit`. To manually run all hooks:
```bash
uv run pre-commit run --all-files
```

Configured hooks:
- `ruff check` - Linting
- `ruff format` - Code formatting
- `ty` - Type checking
- `pytest` - Unit tests

### Running Tests

```bash
uv run pytest
```

### Running Tests with Coverage

```bash
uv run pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Linting

```bash
uv run ruff check .
```

### Auto-fix Linting Issues

```bash
uv run ruff check --fix .
```

### Format Code

```bash
uv run ruff format .
```

### Type Checking

```bash
uv run ty check app/
```

## Project Structure

```
odoo-api-connector/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration settings
│   └── odoo_client.py    # Odoo API client
├── tests/
│   ├── __init__.py
│   ├── test_api.py       # Functional tests
│   └── test_odoo_client.py # Unit tests
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

## Configuration

The application can be configured using environment variables:

- `ODOO_URL`: Odoo server URL (default: `http://localhost:8069`)
- `ODOO_DB`: Odoo database name (default: `odoo`)
- `ODOO_USERNAME`: Odoo username (default: `admin`)
- `ODOO_PASSWORD`: Odoo password (default: `admin`)
- `ODOO_API_KEY`: Odoo API key (optional, alternative to username/password authentication)

**Note**: If `ODOO_API_KEY` is provided, it will be used for authentication instead of username/password.

## Security

This API includes basic hardening middleware and a per-client rate limiter.

### Rate limiting

Rate limiting is enabled by default (per IP).

- `API_ENABLE_RATE_LIMIT`: Enable/disable rate limiting (default: `true`)
- `API_RATE_LIMIT_DEFAULT`: Default limit string (default: `60/minute`)

Example:
```bash
API_ENABLE_RATE_LIMIT=true
API_RATE_LIMIT_DEFAULT="10/minute"
```

### Security headers

Security headers are enabled by default.

- `API_ENABLE_SECURITY_HEADERS`: Enable/disable security headers (default: `true`)

Currently sets (when not already present):
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Request body size limit

The API can reject requests with large bodies using the `Content-Length` header.

- `API_ENABLE_MAX_BODY_SIZE`: Enable/disable max body size check (default: `true`)
- `API_MAX_REQUEST_BODY_BYTES`: Max allowed request size in bytes (default: `1048576` = 1 MiB)

### Allowed hosts

Optionally restrict the `Host` header.

- `API_ALLOWED_HOSTS`: List of allowed hosts (default: `["*"]`)

Example (Pydantic expects JSON for list values):
```bash
API_ALLOWED_HOSTS='["example.com","api.example.com"]'
```

### CORS

- `API_CORS_ORIGINS`: List of allowed CORS origins (default: `["*"]`)

Example (Pydantic expects JSON for list values):
```bash
API_CORS_ORIGINS='["https://example.com"]'
```

## License

MIT
