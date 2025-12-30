"""Functional tests for FastAPI endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestEndpoints:
    """Test cases for API endpoints."""

    def test_root_endpoint(self) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Odoo API Connector"}

    def test_users_endpoint_success(self) -> None:
        """Test successful users endpoint."""
        mock_users = [
            {"id": 1, "name": "Admin", "login": "admin", "email": "admin@example.com"},
            {"id": 2, "name": "User1", "login": "user1", "email": "user1@example.com"},
        ]

        with patch("app.main.OdooClient") as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.get_users.return_value = mock_users
            mock_client_class.return_value = mock_instance

            response = client.get("/users")

            assert response.status_code == 200
            assert response.json() == mock_users
            mock_instance.get_users.assert_called_once()

    def test_users_endpoint_failure(self) -> None:
        """Test users endpoint failure."""
        with patch("app.main.OdooClient") as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.get_users.side_effect = Exception("Connection error")
            mock_client_class.return_value = mock_instance

            response = client.get("/users")

            assert response.status_code == 500
            assert "Failed to get users" in response.json()["detail"]
            assert "Connection error" in response.json()["detail"]


@pytest.mark.asyncio
class TestEndpointsAsync:
    """Async test cases for API endpoints."""

    async def test_users_endpoint_async(self) -> None:
        """Test users endpoint with async test."""
        mock_users = [
            {"id": 1, "name": "Admin", "login": "admin", "email": "admin@example.com"},
        ]

        with patch("app.main.OdooClient") as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.get_users.return_value = mock_users
            mock_client_class.return_value = mock_instance

            response = client.get("/users")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Admin"
