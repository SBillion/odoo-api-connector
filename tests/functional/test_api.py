"""Functional tests for FastAPI endpoints."""

from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app, get_odoo_client


@pytest.fixture()
def app() -> Generator[FastAPI]:
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
        assert (
            response.headers.get("permissions-policy") == "geolocation=(), microphone=(), camera=()"
        )
        assert (
            response.headers.get("strict-transport-security")
            == "max-age=31536000; includeSubDomains"
        )

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

        # Send a POST request with body exceeding the limit
        # Middleware rejects before endpoint routing, so endpoint method doesn't matter
        large_body = "x" * 200
        response = test_client.post("/", content=large_body)
        assert response.status_code == 413
        assert response.text == "Request body too large"

    def test_max_body_size_within_limit(self) -> None:
        """Test that requests within max body size pass through the middleware."""
        test_app = create_app(
            Settings(
                api_max_request_body_bytes=100,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        test_client = TestClient(test_app)

        # Send a POST request with body within the limit
        # Middleware should allow it through (endpoint will return 405 since root only accepts GET)
        small_body = "x" * 50
        response = test_client.post("/", content=small_body)
        # We expect 405 (Method Not Allowed) because root endpoint doesn't accept POST
        # This proves the middleware passed it through without rejecting for size
        assert response.status_code == 405

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

    async def test_root_endpoint_cors_headers(self, app: FastAPI, client: TestClient) -> None:
        """Test CORS headers on root endpoint."""
        response = client.get("/", headers={"Origin": "http://example.com"})
        assert response.status_code == 200
        # CORS should be configured based on app settings

    async def test_contacts_endpoint_cors_preflight(self, app: FastAPI, client: TestClient) -> None:
        """Test CORS preflight request for contacts endpoint."""
        response = client.options(
            "/contacts",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200

    async def test_get_contact_by_id_cors_preflight(self, app: FastAPI, client: TestClient) -> None:
        """Test CORS preflight request for get contact by ID endpoint."""
        response = client.options(
            "/contacts/1",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200

    async def test_contacts_endpoint_with_multiple_results(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test contacts endpoint with multiple results."""
        mock_contacts = [
            {
                "id": i,
                "name": f"Contact {i}",
                "email": f"contact{i}@example.com",
                "phone": f"12345{i}",
                "company_name": f"Company {i}",
            }
            for i in range(1, 6)
        ]

        mock_client = AsyncMock()
        mock_client.get_contacts.return_value = mock_contacts

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 5
            for i, contact in enumerate(data, 1):
                assert contact["name"] == f"Contact {i}"
        finally:
            app.dependency_overrides.clear()

    async def test_get_contact_by_id_with_special_characters(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test get contact by ID with special characters in data."""
        mock_contact = {
            "id": 1,
            "name": "José García-López",
            "email": "josé@example.com",
            "phone": "+33 (0) 1 23 45 67 89",
            "company_name": "Société Générale",
        }

        mock_client = AsyncMock()
        mock_client.get_contact_by_id.return_value = mock_contact

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts/1")

            assert response.status_code == 200
            assert response.json() == mock_contact
        finally:
            app.dependency_overrides.clear()

    async def test_contacts_endpoint_preserves_data_types(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test that contacts endpoint preserves data types."""
        mock_contacts = [
            {
                "id": 1,
                "name": "Contact 1",
                "email": "contact1@example.com",
                "phone": "123456",
                "company_name": "Company 1",
            }
        ]

        mock_client = AsyncMock()
        mock_client.get_contacts.return_value = mock_contacts

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data[0]["id"], int)
            assert isinstance(data[0]["name"], str)
            assert isinstance(data[0]["email"], str)
        finally:
            app.dependency_overrides.clear()

    async def test_get_contact_by_id_with_different_ids(self, app: FastAPI) -> None:
        """Test get contact by ID with various contact IDs."""
        test_app = create_app(
            Settings(
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        test_client = TestClient(test_app)

        for contact_id in [1, 100, 999]:
            mock_contact = {
                "id": contact_id,
                "name": f"Contact {contact_id}",
                "email": f"contact{contact_id}@example.com",
                "phone": f"555-000{contact_id}",
                "company_name": "Test Co",
            }

            mock_client = AsyncMock()
            mock_client.get_contact_by_id.return_value = mock_contact

            test_app.dependency_overrides[get_odoo_client] = lambda: mock_client

            try:
                response = test_client.get(f"/contacts/{contact_id}")

                assert response.status_code == 200
                assert response.json()["id"] == contact_id
            finally:
                test_app.dependency_overrides.clear()

    async def test_endpoints_return_json_content_type(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test that endpoints return JSON content type."""
        # Test root endpoint
        response = client.get("/")
        assert response.headers.get("content-type") == "application/json"

        # Test contacts endpoint with mock
        mock_client = AsyncMock()
        mock_client.get_contacts.return_value = []

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts")
            assert response.headers.get("content-type") == "application/json"
        finally:
            app.dependency_overrides.clear()

    async def test_security_headers_on_all_endpoints(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test that security headers are present on all endpoints."""
        endpoints = ["/", "/contacts"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.headers.get("x-content-type-options") == "nosniff"
            assert response.headers.get("x-frame-options") == "DENY"
            assert response.headers.get("referrer-policy") == "no-referrer"

    async def test_rate_limiting_with_contact_endpoint(self, app: FastAPI) -> None:
        """Test rate limiting on contacts endpoint."""
        test_app = create_app(
            Settings(
                api_rate_limit_default="1/minute",
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        test_client = TestClient(test_app)

        mock_client = AsyncMock()
        mock_client.get_contacts.return_value = []

        test_app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            # First request should succeed
            response1 = test_client.get("/contacts")
            assert response1.status_code == 200

            # Second request should be rate limited
            response2 = test_client.get("/contacts")
            assert response2.status_code == 429
        finally:
            test_app.dependency_overrides.clear()

    async def test_get_contact_by_id_string_id_converted_to_int(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test that contact ID is properly converted to int."""
        mock_contact = {
            "id": 42,
            "name": "Test Contact",
            "email": "test@example.com",
            "phone": "123456",
            "company_name": "Test",
        }

        mock_client = AsyncMock()
        mock_client.get_contact_by_id.return_value = mock_contact

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts/42")

            assert response.status_code == 200
            # Verify mock was called with integer, not string
            mock_client.get_contact_by_id.assert_called_once_with(42)
        finally:
            app.dependency_overrides.clear()

    async def test_contacts_endpoint_empty_list(self, app: FastAPI, client: TestClient) -> None:
        """Test contacts endpoint when no contacts exist."""
        mock_client = AsyncMock()
        mock_client.get_contacts.return_value = []

        app.dependency_overrides[get_odoo_client] = lambda: mock_client

        try:
            response = client.get("/contacts")

            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()

    async def test_root_endpoint_response_structure(self, app: FastAPI, client: TestClient) -> None:
        """Test root endpoint response structure."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0
