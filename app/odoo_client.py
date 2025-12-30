"""Odoo API client module."""

from typing import Any

import httpx

from app.config import settings


class OdooClient:
    """Client for interacting with Odoo API."""

    def __init__(
        self,
        url: str | None = None,
        db: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize Odoo client.

        Args:
            url: Odoo server URL
            db: Database name
            username: Username for authentication
            password: Password for authentication
        """
        self.url = url or settings.odoo_url
        self.db = db or settings.odoo_db
        self.username = username or settings.odoo_username
        self.password = password or settings.odoo_password
        self._uid: int | None = None
        self._session_id: str | None = None
        # Reusable HTTP client
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            AsyncClient instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def authenticate(self) -> int:
        """Authenticate with Odoo and get user ID.

        Returns:
            User ID after successful authentication

        Raises:
            httpx.HTTPError: If authentication fails
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.url}/web/session/authenticate",
            json={
                "jsonrpc": "2.0",
                "params": {
                    "db": self.db,
                    "login": self.username,
                    "password": self.password,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise httpx.HTTPError(f"Authentication failed: {data['error']}")

        result = data.get("result", {})
        uid = result.get("uid")

        if not uid:
            raise httpx.HTTPError("Authentication failed: No user ID returned")

        self._uid = uid
        # Store session ID from cookies if available
        if "session_id" in response.cookies:
            self._session_id = response.cookies["session_id"]

        return uid

    async def get_users(self) -> list[dict[str, Any]]:
        """Get list of users from Odoo.

        Returns:
            List of user dictionaries

        Raises:
            httpx.HTTPError: If request fails
        """
        if not self._uid:
            await self.authenticate()

        client = await self._get_client()
        response = await client.post(
            f"{self.url}/web/dataset/call_kw",
            json={
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "res.users",
                    "method": "search_read",
                    "args": [[]],
                    "kwargs": {
                        "fields": ["id", "name", "login", "email"],
                    },
                },
                "id": 1,
            },
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise httpx.HTTPError(f"Failed to get users: {data['error']}")

        return data.get("result", [])

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

