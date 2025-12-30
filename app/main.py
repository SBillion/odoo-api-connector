"""FastAPI application main module."""

from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException

from app.odoo_client import OdooClient

app = FastAPI(
    title="Odoo API Connector",
    description="A FastAPI connector to interact with Odoo API",
    version="0.1.0",
)

# Singleton instance for OdooClient
_odoo_client: OdooClient | None = None


def get_odoo_client() -> OdooClient:
    """Get or create OdooClient instance.

    Returns:
        OdooClient instance
    """
    global _odoo_client
    if _odoo_client is None:
        _odoo_client = OdooClient()
    return _odoo_client


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Welcome message
    """
    return {"message": "Welcome to Odoo API Connector"}


@app.get("/users")
async def get_users(
    client: Annotated[OdooClient, Depends(get_odoo_client)]
) -> list[dict[str, Any]]:
    """Get users from Odoo API.

    Args:
        client: Injected OdooClient instance

    Returns:
        List of users from Odoo

    Raises:
        HTTPException: If failed to retrieve users
    """
    try:
        users = await client.get_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

