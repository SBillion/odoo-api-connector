"""FastAPI application main module."""

from typing import Any

from fastapi import FastAPI, HTTPException

from app.odoo_client import OdooClient

app = FastAPI(
    title="Odoo API Connector",
    description="A FastAPI connector to interact with Odoo API",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Welcome message
    """
    return {"message": "Welcome to Odoo API Connector"}


@app.get("/users")
async def get_users() -> list[dict[str, Any]]:
    """Get users from Odoo API.

    Returns:
        List of users from Odoo

    Raises:
        HTTPException: If failed to retrieve users
    """
    client = OdooClient()
    try:
        users = await client.get_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")
