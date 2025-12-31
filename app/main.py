"""FastAPI application main module."""

from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import Settings, settings
from app.odoo_client import OdooClient
from app.security import MaxBodySizeMiddleware, SecurityHeadersMiddleware


def create_app(settings_override: Settings | None = None) -> FastAPI:
    active_settings = settings_override or settings

    app = FastAPI(
        title="Odoo API Connector",
        description="A FastAPI connector to interact with Odoo API",
        version="0.1.0",
    )

    if active_settings.api_allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=active_settings.api_allowed_hosts)

    if active_settings.api_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=active_settings.api_cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

    if active_settings.api_enable_security_headers:
        app.add_middleware(SecurityHeadersMiddleware)

    if active_settings.api_enable_max_body_size:
        app.add_middleware(
            MaxBodySizeMiddleware, max_body_size_bytes=active_settings.api_max_request_body_bytes
        )

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[active_settings.api_rate_limit_default],
        enabled=active_settings.api_enable_rate_limit,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    if active_settings.api_enable_rate_limit:
        app.add_middleware(SlowAPIMiddleware)

    @app.get("/")
    @limiter.limit(active_settings.api_rate_limit_default)
    async def root(request: Request) -> dict[str, str]:
        """Root endpoint.

        Returns:
            Welcome message
        """

        return {"message": "Welcome to Odoo API Connector"}

    @app.get("/contacts")
    @limiter.limit(active_settings.api_rate_limit_default)
    async def get_contacts(
        request: Request,
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
    @limiter.limit(active_settings.api_rate_limit_default)
    async def get_contact_by_id(
        request: Request,
        contact_id: int,
        client: Annotated[OdooClient, Depends(get_odoo_client)],
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

    return app

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


app = create_app()
