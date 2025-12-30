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
    async def test_get_contacts_success(self) -> None:
        """Test successful retrieval of contacts."""
        # Mock authentication
        auth_response = MagicMock()
        auth_response.json.return_value = {"result": {"uid": 123}}
        auth_response.raise_for_status = MagicMock()
        auth_response.cookies = {}

        # Mock get contacts
        contacts_response = MagicMock()
        contacts_response.json.return_value = {
            "result": [
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
        }
        contacts_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[auth_response, contacts_response])
            mock_get_client.return_value = mock_client

            client = OdooClient()
            contacts = await client.get_contacts()

            assert len(contacts) == 2
            assert contacts[0]["name"] == "John Doe"
            assert contacts[1]["name"] == "Jane Smith"

    @pytest.mark.asyncio
    async def test_get_contacts_with_existing_uid(self) -> None:
        """Test getting contacts when already authenticated."""
        contacts_response = MagicMock()
        contacts_response.json.return_value = {
            "result": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "123456",
                    "company_name": "Acme",
                },
            ]
        }
        contacts_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=contacts_response)
            mock_get_client.return_value = mock_client

            client = OdooClient()
            client._uid = 123  # Set UID to skip authentication

            contacts = await client.get_contacts()

            assert len(contacts) == 1
            # Verify only one call was made (no authentication call)
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contacts_failure(self) -> None:
        """Test failure when getting contacts."""
        # Mock authentication
        auth_response = MagicMock()
        auth_response.json.return_value = {"result": {"uid": 123}}
        auth_response.raise_for_status = MagicMock()
        auth_response.cookies = {}

        # Mock get contacts with error
        contacts_response = MagicMock()
        contacts_response.json.return_value = {
            "error": {
                "message": "Access denied",
            }
        }
        contacts_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[auth_response, contacts_response])
            mock_get_client.return_value = mock_client

            client = OdooClient()
            with pytest.raises(httpx.HTTPError, match="Failed to get contacts"):
                await client.get_contacts()

    @pytest.mark.asyncio
    async def test_get_contact_by_id_success(self) -> None:
        """Test successful retrieval of a contact by ID."""
        # Mock authentication
        auth_response = MagicMock()
        auth_response.json.return_value = {"result": {"uid": 123}}
        auth_response.raise_for_status = MagicMock()
        auth_response.cookies = {}

        # Mock get contact by ID
        contact_response = MagicMock()
        contact_response.json.return_value = {
            "result": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "123456",
                    "company_name": "Acme",
                }
            ]
        }
        contact_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[auth_response, contact_response])
            mock_get_client.return_value = mock_client

            client = OdooClient()
            contact = await client.get_contact_by_id(1)

            assert contact["id"] == 1
            assert contact["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_get_contact_by_id_not_found(self) -> None:
        """Test get contact by ID when contact is not found."""
        from fastapi import HTTPException

        # Mock authentication
        auth_response = MagicMock()
        auth_response.json.return_value = {"result": {"uid": 123}}
        auth_response.raise_for_status = MagicMock()
        auth_response.cookies = {}

        # Mock get contact by ID with empty result
        contact_response = MagicMock()
        contact_response.json.return_value = {"result": []}
        contact_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[auth_response, contact_response])
            mock_get_client.return_value = mock_client

            client = OdooClient()
            with pytest.raises(HTTPException) as exc_info:
                await client.get_contact_by_id(999)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_contact_by_id_with_existing_uid(self) -> None:
        """Test getting contact by ID when already authenticated."""
        contact_response = MagicMock()
        contact_response.json.return_value = {
            "result": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "123456",
                    "company_name": "Acme",
                }
            ]
        }
        contact_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=contact_response)
            mock_get_client.return_value = mock_client

            client = OdooClient()
            client._uid = 123  # Set UID to skip authentication

            contact = await client.get_contact_by_id(1)

            assert contact["id"] == 1
            # Verify only one call was made (no authentication call)
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contact_by_id_failure(self) -> None:
        """Test failure when getting contact by ID."""
        # Mock authentication
        auth_response = MagicMock()
        auth_response.json.return_value = {"result": {"uid": 123}}
        auth_response.raise_for_status = MagicMock()
        auth_response.cookies = {}

        # Mock get contact by ID with error
        contact_response = MagicMock()
        contact_response.json.return_value = {
            "error": {
                "message": "Access denied",
            }
        }
        contact_response.raise_for_status = MagicMock()

        with patch.object(OdooClient, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[auth_response, contact_response])
            mock_get_client.return_value = mock_client

            client = OdooClient()
            with pytest.raises(httpx.HTTPError, match="Failed to get contact"):
                await client.get_contact_by_id(1)

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

    def test_init_with_api_key(self) -> None:
        """Test client initialization with API key."""
        client = OdooClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key(self) -> None:
        """Test authentication with API key skips traditional auth."""
        client = OdooClient(api_key="test-api-key")

        # Should not make any HTTP calls when API key is present
        uid = await client.authenticate()

        assert uid == 1  # Placeholder UID
        assert client._uid == 1

    @pytest.mark.asyncio
    async def test_get_client_with_api_key(self) -> None:
        """Test that API key is added to headers."""
        client = OdooClient(api_key="test-api-key")

        http_client = await client._get_client()

        assert "api-key" in http_client.headers
        assert http_client.headers["api-key"] == "test-api-key"

        await client.close()
