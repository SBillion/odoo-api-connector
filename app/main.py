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


@app.get("/contacts")
async def get_contacts(
    client: Annotated[OdooClient, Depends(get_odoo_client)],
) -> list[dict[str, Any]]:
    """Get contacts from Odoo API.

    Args:
        client: Injected OdooClient instance

    Returns:
        List of contacts from Odoo

    Raises:
        HTTPException: If failed to retrieve contacts
    """
    try:
        contacts = await client.get_contacts()
        return contacts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contacts: {str(e)}")


@app.get("/contacts/{contact_id}")
async def get_contact_by_id(
    contact_id: int, client: Annotated[OdooClient, Depends(get_odoo_client)]
) -> dict[str, Any]:
    """Get a specific contact by ID from Odoo API.

    Args:
        contact_id: ID of the contact to retrieve
        client: Injected OdooClient instance

    Returns:
        Contact data

    Raises:
        HTTPException: If failed to retrieve contact or contact not found
    """
    try:
        contact = await client.get_contact_by_id(contact_id)
        return contact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contact: {str(e)}")
