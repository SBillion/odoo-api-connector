"""Functional tests for FastAPI endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_odoo_client

client = TestClient(app)


class TestEndpoints:
    """Test cases for API endpoints."""

    def test_root_endpoint(self) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Odoo API Connector"}

    def test_contacts_endpoint_success(self) -> None:
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

    def test_contacts_endpoint_failure(self) -> None:
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

    def test_get_contact_by_id_success(self) -> None:
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

    def test_get_contact_by_id_not_found(self) -> None:
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

    def test_get_contact_by_id_failure(self) -> None:
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

    async def test_contacts_endpoint_async(self) -> None:
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
