"""Security middlewares and helpers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )

        # Only meaningful over HTTPS; harmless over HTTP.
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_body_size_bytes: int) -> None:
        super().__init__(app)
        self.max_body_size_bytes = max_body_size_bytes

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_body_size_bytes:
                    return Response(status_code=413, content="Request body too large")
            except ValueError:
                return Response(status_code=400, content="Invalid Content-Length header")

        return await call_next(request)


async def rate_limit_handler(request: Request | object, exc: Exception) -> Response:  # type: ignore[misc]
    """Handle rate limit exceeded errors.

    Args:
        request: The request that exceeded rate limit
        exc: The RateLimitExceeded exception

    Returns:
        429 Too Many Requests response
    """
    return Response(
        status_code=429,
        content="Rate limit exceeded",
        headers={"Retry-After": "60"},
    )
