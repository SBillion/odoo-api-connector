"""Unit tests for Odoo client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.odoo_client import OdooClient


class TestOdooClient:
    """Test cases for OdooClient."""

    def test_init_with_defaults(self) -> None:
        """Test client initialization with default settings."""
        client = OdooClient()
        assert client.url == "http://localhost:8069"
        assert client.db == "odoo"
        assert client.username == "admin"
        assert client.password == "admin"
        assert client._uid is None

    def test_init_with_custom_values(self) -> None:
        """Test client initialization with custom values."""
        client = OdooClient(
            url="http://test:8080",
            db="testdb",
            username="testuser",
            password="testpass",
        )
        assert client.url == "http://test:8080"
        assert client.db == "testdb"
        assert client.username == "testuser"
        assert client.password == "testpass"

    @pytest.mark.asyncio
    async def test_authenticate_success(self) -> None:
        """Test successful authentication."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "uid": 123,
                "username": "admin",
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_response.cookies = {}

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client = OdooClient()
            uid = await client.authenticate()

            assert uid == 123
            assert client._uid == 123

    @pytest.mark.asyncio
    async def test_authenticate_failure_with_error(self) -> None:
        """Test authentication failure with error response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid credentials",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client = OdooClient()
            with pytest.raises(httpx.HTTPError, match="Authentication failed"):
                await client.authenticate()

    @pytest.mark.asyncio
    async def test_authenticate_failure_no_uid(self) -> None:
        """Test authentication failure when no UID is returned."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            client = OdooClient()
            with pytest.raises(httpx.HTTPError, match="No user ID returned"):
                await client.authenticate()

    @pytest.mark.asyncio
    async def test_get_users_success(self) -> None:
        """Test successful retrieval of users."""
        # Mock authentication
        auth_response = MagicMock()
        auth_response.json.return_value = {"result": {"uid": 123}}
        auth_response.raise_for_status = MagicMock()
        auth_response.cookies = {}

        # Mock get users
        users_response = MagicMock()
        users_response.json.return_value = {
            "result": [
                {"id": 1, "name": "Admin", "login": "admin", "email": "admin@example.com"},
                {"id": 2, "name": "User1", "login": "user1", "email": "user1@example.com"},
            ]
        }
        users_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[auth_response, users_response])
            mock_get_client.return_value = mock_client

            client = OdooClient()
            users = await client.get_users()

            assert len(users) == 2
            assert users[0]["name"] == "Admin"
            assert users[1]["name"] == "User1"

    @pytest.mark.asyncio
    async def test_get_users_with_existing_uid(self) -> None:
        """Test getting users when already authenticated."""
        users_response = MagicMock()
        users_response.json.return_value = {
            "result": [
                {"id": 1, "name": "Admin", "login": "admin", "email": "admin@example.com"},
            ]
        }
        users_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=users_response)
            mock_get_client.return_value = mock_client

            client = OdooClient()
            client._uid = 123  # Set UID to skip authentication

            users = await client.get_users()

            assert len(users) == 1
            # Verify only one call was made (no authentication call)
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_users_failure(self) -> None:
        """Test failure when getting users."""
        # Mock authentication
        auth_response = MagicMock()
        auth_response.json.return_value = {"result": {"uid": 123}}
        auth_response.raise_for_status = MagicMock()
        auth_response.cookies = {}

        # Mock get users with error
        users_response = MagicMock()
        users_response.json.return_value = {
            "error": {
                "message": "Access denied",
            }
        }
        users_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[auth_response, users_response])
            mock_get_client.return_value = mock_client

            client = OdooClient()
            with pytest.raises(httpx.HTTPError, match="Failed to get users"):
                await client.get_users()

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test closing the client."""
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()

        client = OdooClient()
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None

