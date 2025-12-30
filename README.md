# odoo-api-connector

A FastAPI connector to interact with Odoo API

## Features

- FastAPI application with `/users` endpoint
- Odoo API client with authentication
- Full type hints support
- Unit and functional tests
- Test coverage reporting
- Linting with Ruff
- Docker support with docker-compose

## Requirements

- Python 3.12+
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

### Using UV (Development)

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Using Docker Compose

```bash
docker-compose up -d
```

This will start:
- Odoo server on `http://localhost:8069`
- PostgreSQL database
- FastAPI application on `http://localhost:8000`

## API Endpoints

### GET /
Root endpoint returning a welcome message.

### GET /users
Get list of users from Odoo API.

Returns a list of user objects with fields: `id`, `name`, `login`, `email`.

## Development

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

## License

MIT
