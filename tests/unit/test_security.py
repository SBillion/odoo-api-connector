"""Unit tests for security middlewares."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.security import rate_limit_handler


class TestSecurityHeadersMiddleware:
    """Test cases for SecurityHeadersMiddleware."""

    def test_security_headers_added_to_response(self) -> None:
        """Test that security headers are added to successful responses."""
        app = create_app(
            Settings(
                api_enable_security_headers=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") == "no-referrer"
        assert (
            response.headers.get("permissions-policy") == "geolocation=(), microphone=(), camera=()"
        )
        assert (
            response.headers.get("strict-transport-security")
            == "max-age=31536000; includeSubDomains"
        )

    def test_security_headers_not_overwritten(self) -> None:
        """Test that security headers are not overwritten if already present."""
        app = create_app(
            Settings(
                api_enable_security_headers=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        # Multiple requests should have consistent headers
        response1 = client.get("/")
        response2 = client.get("/")

        assert response1.headers.get("x-content-type-options") == "nosniff"
        assert response2.headers.get("x-content-type-options") == "nosniff"

    def test_security_headers_on_error_responses(self) -> None:
        """Test that security headers are added even on error responses."""
        app = create_app(
            Settings(
                api_enable_security_headers=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        # Request to non-existent endpoint
        response = client.get("/nonexistent")

        assert response.status_code == 404
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_security_headers_content_length(self) -> None:
        """Test that security headers don't interfere with content-length."""
        app = create_app(
            Settings(
                api_enable_security_headers=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        assert "content-length" in response.headers or "transfer-encoding" in response.headers


class TestMaxBodySizeMiddleware:
    """Test cases for MaxBodySizeMiddleware."""

    def test_request_exceeding_max_body_size(self) -> None:
        """Test that requests exceeding max body size are rejected."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=100,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        large_body = "x" * 200
        response = client.post("/", content=large_body)

        assert response.status_code == 413
        assert response.text == "Request body too large"

    def test_request_within_max_body_size(self) -> None:
        """Test that requests within max body size pass through."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=200,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        small_body = "x" * 50
        response = client.post("/", content=small_body)

        # We expect 405 (Method Not Allowed) because root endpoint doesn't accept POST
        # This proves the middleware passed it through without rejecting for size
        assert response.status_code == 405

    def test_request_with_invalid_content_length(self) -> None:
        """Test that requests with invalid Content-Length header return 400."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=100,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        response = client.get("/", headers={"Content-Length": "invalid"})

        assert response.status_code == 400
        assert response.text == "Invalid Content-Length header"

    def test_request_without_content_length_header(self) -> None:
        """Test that requests without Content-Length header are allowed."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=100,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200

    def test_max_body_size_with_exact_limit(self) -> None:
        """Test request with body size exactly equal to max limit."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=50,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        # Create body with exactly 50 bytes
        body = "x" * 50
        response = client.post("/", content=body)

        # Should pass the middleware, fail on endpoint (405)
        assert response.status_code == 405

    def test_max_body_size_disabled(self) -> None:
        """Test that max body size check is skipped when disabled."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=10,
                api_enable_max_body_size=False,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        large_body = "x" * 200
        response = client.post("/", content=large_body)

        # Should pass middleware and fail on endpoint
        assert response.status_code == 405

    def test_max_body_size_with_json_content(self) -> None:
        """Test max body size check with JSON content."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=50,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        large_json = {"data": "x" * 200}
        response = client.post("/", json=large_json)

        assert response.status_code == 413


class TestRateLimiting:
    """Test cases for rate limiting."""

    def test_rate_limiting_on_root_endpoint(self) -> None:
        """Test rate limiting on root endpoint."""
        app = create_app(
            Settings(
                api_rate_limit_default="2/minute",
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        client = TestClient(app)

        # First two requests should succeed
        assert client.get("/").status_code == 200
        assert client.get("/").status_code == 200

        # Third request should be rate limited
        response = client.get("/")
        assert response.status_code == 429

    def test_rate_limiting_retry_after_header(self) -> None:
        """Test that rate limit response includes Retry-After header."""
        app = create_app(
            Settings(
                api_rate_limit_default="1/minute",
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        client = TestClient(app)

        # First request succeeds
        client.get("/")

        # Second request is rate limited
        response = client.get("/")

        assert response.status_code == 429
        assert "retry-after" in response.headers

    def test_rate_limiting_different_endpoints(self) -> None:
        """Test that rate limiting applies to all endpoints."""
        app = create_app(
            Settings(
                api_rate_limit_default="1/minute",
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        client = TestClient(app)

        # Use the root endpoint once
        assert client.get("/").status_code == 200

        # Second request from same IP should be rate limited
        response = client.get("/")
        assert response.status_code == 429

    def test_rate_limiting_disabled(self) -> None:
        """Test that rate limiting can be disabled."""
        app = create_app(
            Settings(
                api_enable_rate_limit=False,
                api_rate_limit_default="1/minute",
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        client = TestClient(app)

        # All requests should succeed even with limit of 1/minute
        assert client.get("/").status_code == 200
        assert client.get("/").status_code == 200
        assert client.get("/").status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_handler(self) -> None:
        """Test rate limit handler returns correct response."""

        request = MagicMock()
        exc = MagicMock()

        response = await rate_limit_handler(request, exc)

        assert response.status_code == 429
        assert response.headers.get("Retry-After") == "60"


class TestMiddlewareCombinations:
    """Test cases for middleware interactions."""

    def test_all_middleware_enabled(self) -> None:
        """Test that all middleware work together correctly."""
        app = create_app(
            Settings(
                api_enable_rate_limit=True,
                api_rate_limit_default="10/minute",
                api_enable_security_headers=True,
                api_enable_max_body_size=True,
                api_max_request_body_bytes=1000,
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        client = TestClient(app)

        # Request should pass all middleware
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_max_body_size_checked_before_endpoint(self) -> None:
        """Test that max body size is checked before reaching endpoint."""
        app = create_app(
            Settings(
                api_max_request_body_bytes=10,
                api_enable_max_body_size=True,
                api_allowed_hosts=["testserver"],
            )
        )
        client = TestClient(app)

        # Body too large should be rejected before endpoint is invoked
        response = client.post("/", content="x" * 100)

        assert response.status_code == 413
        assert response.text == "Request body too large"

    def test_security_headers_after_rate_limit(self) -> None:
        """Test that security headers are added even after rate limiting."""
        app = create_app(
            Settings(
                api_rate_limit_default="1/minute",
                api_enable_security_headers=True,
                api_allowed_hosts=["testserver"],
                api_cors_origins=["*"],
            )
        )
        client = TestClient(app)

        # First request succeeds
        response1 = client.get("/")
        assert response1.status_code == 200
        assert response1.headers.get("x-content-type-options") == "nosniff"

        # Second request is rate limited but should still have security headers
        response2 = client.get("/")
        assert response2.status_code == 429
        assert response2.headers.get("x-content-type-options") == "nosniff"
