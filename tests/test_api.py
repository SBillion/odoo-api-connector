"""Functional tests for FastAPI endpoints."""

from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app, get_odoo_client


@pytest.fixture()
def app() -> Generator[FastAPI, None, None]:
    app_instance = create_app(
        Settings(
            api_rate_limit_default="2/minute",
            api_allowed_hosts=["testserver"],
            api_cors_origins=["*"],
        )
    )
    yield app_instance


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestEndpoints:
    """Test cases for API endpoints."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Odoo API Connector"}

    def test_security_headers_present(self, client: TestClient) -> None:
        """Test that security headers are present on the root endpoint response."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") == "no-referrer"
        assert response.headers.get("permissions-policy") == "geolocation=(), microphone=(), camera=()"
        assert response.headers.get("strict-transport-security") == "max-age=31536000; includeSubDomains"

    def test_rate_limiting(self, client: TestClient) -> None:
        """Test that the root endpoint is rate limited after repeated requests."""
        # Create a fresh app instance to avoid rate limiter state interference
        test_app = create_app(
            Settings(
                api_rate_limit_default="2/minute",
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        test_client = TestClient(test_app)
        
        assert test_client.get("/").status_code == 200
        assert test_client.get("/").status_code == 200
        response = test_client.get("/")
        assert response.status_code == 429

    def test_max_body_size_exceeded(self) -> None:
        """Test that requests exceeding max body size are rejected with 413."""
        test_app = create_app(
            Settings(
                api_max_request_body_bytes=100,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        test_client = TestClient(test_app)
        
        # Send a request with Content-Length header exceeding the limit
        large_body = "x" * 200
        response = test_client.post("/", content=large_body)
        assert response.status_code == 413
        assert response.text == "Request body too large"

    def test_max_body_size_within_limit(self) -> None:
        """Test that requests within max body size are accepted."""
        test_app = create_app(
            Settings(
                api_max_request_body_bytes=100,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        test_client = TestClient(test_app)
        
        # Send a request with Content-Length header within the limit
        small_body = "x" * 50
        response = test_client.get("/", content=small_body)
        assert response.status_code == 200

    def test_invalid_content_length_header(self) -> None:
        """Test that requests with invalid Content-Length headers return 400."""
        test_app = create_app(
            Settings(
                api_max_request_body_bytes=100,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        test_client = TestClient(test_app)
        
        # Send a request with an invalid Content-Length header
        response = test_client.get("/", headers={"Content-Length": "invalid"})
        assert response.status_code == 400
        assert response.text == "Invalid Content-Length header"

    def test_contacts_endpoint_success(self, app: FastAPI, client: TestClient) -> None:
        """Test successful contacts endpoint."""
        mock_contacts = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123456",
                "company_name": "Acme",
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "789012",
                "company_name": "Tech Co",
            },
        ]

        mock_client = AsyncMock()
        mock_client.get_contacts.return_value = mock_contacts

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts")

            assert response.status_code == 200
            assert response.json() == mock_contacts
            mock_client.get_contacts.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_contacts_endpoint_failure(self, app: FastAPI, client: TestClient) -> None:
        """Test contacts endpoint failure."""
        mock_client = AsyncMock()
        mock_client.get_contacts.side_effect = Exception("Connection error")

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts")

            assert response.status_code == 500
            assert "Failed to get contacts" in response.json()["detail"]
            assert "Connection error" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_contact_by_id_success(self, app: FastAPI, client: TestClient) -> None:
        """Test successful get contact by ID."""
        mock_contact = {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123456",
            "company_name": "Acme",
        }

        mock_client = AsyncMock()
        mock_client.get_contact_by_id.return_value = mock_contact

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts/1")

            assert response.status_code == 200
            assert response.json() == mock_contact
            mock_client.get_contact_by_id.assert_called_once_with(1)
        finally:
            app.dependency_overrides.clear()

    def test_get_contact_by_id_not_found(self, app: FastAPI, client: TestClient) -> None:
        """Test get contact by ID when contact not found."""
        from fastapi import HTTPException

        mock_client = AsyncMock()
        mock_client.get_contact_by_id.side_effect = HTTPException(
            status_code=404, detail="Contact with ID 999 not found"
        )

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts/999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_contact_by_id_failure(self, app: FastAPI, client: TestClient) -> None:
        """Test get contact by ID failure."""
        mock_client = AsyncMock()
        mock_client.get_contact_by_id.side_effect = Exception("Connection error")

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts/1")

            assert response.status_code == 500
            assert "Failed to get contact" in response.json()["detail"]
            assert "Connection error" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_odoo_client_singleton(self) -> None:
        """Test that get_odoo_client returns singleton instance."""
        # Clear singleton to start fresh
        import app.main

        app.main._odoo_client = None

        client1 = get_odoo_client()
        client2 = get_odoo_client()

        assert client1 is client2


@pytest.mark.asyncio
class TestEndpointsAsync:
    """Async test cases for API endpoints."""

    async def test_contacts_endpoint_async(self, app: FastAPI, client: TestClient) -> None:
        """Test contacts endpoint with async test."""
        mock_contacts = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123456",
                "company_name": "Acme",
            },
        ]

        mock_client = AsyncMock()
        mock_client.get_contacts.return_value = mock_contacts

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "John Doe"
        finally:
            app.dependency_overrides.clear()
