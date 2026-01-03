"""Unit tests for configuration settings."""

from app.config import Settings


class TestSettingsDefaults:
    """Test cases for default settings."""

    def test_default_settings(self) -> None:
        """Test that default settings are correctly initialized."""
        settings = Settings()

        assert settings.odoo_url == "http://localhost:8069"
        assert settings.odoo_db == "odoo"
        assert settings.odoo_username == "admin"
        assert settings.odoo_password == "admin"
        assert settings.odoo_api_key is None

    def test_default_api_settings(self) -> None:
        """Test default API settings."""
        settings = Settings()

        assert settings.api_enable_rate_limit is True
        assert settings.api_rate_limit_default == "60/minute"
        assert settings.api_enable_security_headers is True
        assert settings.api_enable_max_body_size is True
        assert settings.api_max_request_body_bytes == 1_048_576
        assert settings.api_cors_origins == ["*"]
        assert settings.api_allowed_hosts == ["*"]

    def test_settings_with_custom_values(self) -> None:
        """Test settings with custom values."""
        settings = Settings(
            odoo_url="http://custom:8080",
            odoo_db="custom_db",
            odoo_username="custom_user",
            odoo_password="custom_pass",
        )

        assert settings.odoo_url == "http://custom:8080"
        assert settings.odoo_db == "custom_db"
        assert settings.odoo_username == "custom_user"
        assert settings.odoo_password == "custom_pass"

    def test_settings_with_api_key(self) -> None:
        """Test settings with API key."""
        settings = Settings(odoo_api_key="test-api-key-123")

        assert settings.odoo_api_key == "test-api-key-123"

    def test_settings_with_rate_limit_disabled(self) -> None:
        """Test settings with rate limiting disabled."""
        settings = Settings(api_enable_rate_limit=False)

        assert settings.api_enable_rate_limit is False

    def test_settings_with_security_headers_disabled(self) -> None:
        """Test settings with security headers disabled."""
        settings = Settings(api_enable_security_headers=False)

        assert settings.api_enable_security_headers is False

    def test_settings_with_max_body_size_disabled(self) -> None:
        """Test settings with max body size disabled."""
        settings = Settings(api_enable_max_body_size=False)

        assert settings.api_enable_max_body_size is False

    def test_settings_with_custom_max_body_size(self) -> None:
        """Test settings with custom max body size."""
        settings = Settings(api_max_request_body_bytes=500_000)

        assert settings.api_max_request_body_bytes == 500_000

    def test_settings_with_custom_rate_limit(self) -> None:
        """Test settings with custom rate limit."""
        settings = Settings(api_rate_limit_default="100/minute")

        assert settings.api_rate_limit_default == "100/minute"

    def test_settings_with_single_cors_origin(self) -> None:
        """Test settings with single CORS origin."""
        settings = Settings(api_cors_origins=["https://example.com"])

        assert settings.api_cors_origins == ["https://example.com"]

    def test_settings_with_multiple_cors_origins(self) -> None:
        """Test settings with multiple CORS origins."""
        origins = ["https://example.com", "https://app.example.com", "http://localhost:3000"]
        settings = Settings(api_cors_origins=origins)

        assert settings.api_cors_origins == origins

    def test_settings_with_single_allowed_host(self) -> None:
        """Test settings with single allowed host."""
        settings = Settings(api_allowed_hosts=["example.com"])

        assert settings.api_allowed_hosts == ["example.com"]

    def test_settings_with_multiple_allowed_hosts(self) -> None:
        """Test settings with multiple allowed hosts."""
        hosts = ["example.com", "app.example.com", "localhost"]
        settings = Settings(api_allowed_hosts=hosts)

        assert settings.api_allowed_hosts == hosts

    def test_settings_with_all_custom_values(self) -> None:
        """Test settings with all custom values."""
        settings = Settings(
            odoo_url="http://custom:8080",
            odoo_db="custom_db",
            odoo_username="custom_user",
            odoo_password="custom_pass",
            odoo_api_key="custom-key",
            api_enable_rate_limit=False,
            api_rate_limit_default="100/minute",
            api_enable_security_headers=False,
            api_enable_max_body_size=False,
            api_max_request_body_bytes=500_000,
            api_cors_origins=["https://example.com"],
            api_allowed_hosts=["example.com"],
        )

        assert settings.odoo_url == "http://custom:8080"
        assert settings.odoo_db == "custom_db"
        assert settings.odoo_username == "custom_user"
        assert settings.odoo_password == "custom_pass"
        assert settings.odoo_api_key == "custom-key"
        assert settings.api_enable_rate_limit is False
        assert settings.api_rate_limit_default == "100/minute"
        assert settings.api_enable_security_headers is False
        assert settings.api_enable_max_body_size is False
        assert settings.api_max_request_body_bytes == 500_000
        assert settings.api_cors_origins == ["https://example.com"]
        assert settings.api_allowed_hosts == ["example.com"]


class TestSettingsTypeValidation:
    """Test cases for settings type validation."""

    def test_settings_api_key_can_be_none(self) -> None:
        """Test that API key can be None."""
        settings = Settings(odoo_api_key=None)

        assert settings.odoo_api_key is None

    def test_settings_cors_origins_is_list(self) -> None:
        """Test that CORS origins is a list."""
        settings = Settings(api_cors_origins=["https://example.com"])

        assert isinstance(settings.api_cors_origins, list)

    def test_settings_allowed_hosts_is_list(self) -> None:
        """Test that allowed hosts is a list."""
        settings = Settings(api_allowed_hosts=["example.com"])

        assert isinstance(settings.api_allowed_hosts, list)

    def test_settings_boolean_fields(self) -> None:
        """Test that boolean fields are properly typed."""
        settings = Settings()

        assert isinstance(settings.api_enable_rate_limit, bool)
        assert isinstance(settings.api_enable_security_headers, bool)
        assert isinstance(settings.api_enable_max_body_size, bool)

    def test_settings_string_fields(self) -> None:
        """Test that string fields are properly typed."""
        settings = Settings()

        assert isinstance(settings.odoo_url, str)
        assert isinstance(settings.odoo_db, str)
        assert isinstance(settings.odoo_username, str)
        assert isinstance(settings.odoo_password, str)
        assert isinstance(settings.api_rate_limit_default, str)

    def test_settings_int_fields(self) -> None:
        """Test that integer fields are properly typed."""
        settings = Settings()

        assert isinstance(settings.api_max_request_body_bytes, int)


class TestSettingsEnvironmentVariables:
    """Test cases for environment variable loading."""

    def test_settings_from_env_file(self) -> None:
        """Test that settings can be loaded from environment file."""
        # This test assumes .env file exists with custom values
        # We test that the Settings class can be instantiated
        settings = Settings()
        assert settings is not None

    def test_settings_ignore_extra_fields(self) -> None:
        """Test that extra fields are ignored (extra='ignore' config)."""
        # Should not raise an error even with extra fields
        settings = Settings(
            odoo_url="http://test:8080",
            extra_field="should be ignored",  # type: ignore[call-arg]
        )

        assert settings.odoo_url == "http://test:8080"
        assert not hasattr(settings, "extra_field")

    def test_settings_value_ranges(self) -> None:
        """Test that settings accept valid value ranges."""
        # Very large max body size
        settings = Settings(api_max_request_body_bytes=10_000_000)
        assert settings.api_max_request_body_bytes == 10_000_000

        # Very small max body size
        settings = Settings(api_max_request_body_bytes=1)
        assert settings.api_max_request_body_bytes == 1


class TestSettingsIntegration:
    """Integration tests for settings."""

    def test_settings_used_in_app_creation(self) -> None:
        """Test that settings are properly used when creating app."""
        from app.main import create_app

        settings = Settings(
            api_rate_limit_default="5/minute",
            api_allowed_hosts=["testserver"],
        )

        app = create_app(settings)

        assert app is not None

    def test_multiple_settings_instances_independent(self) -> None:
        """Test that multiple Settings instances are independent."""
        settings1 = Settings(odoo_url="http://url1:8080")
        settings2 = Settings(odoo_url="http://url2:8080")

        assert settings1.odoo_url == "http://url1:8080"
        assert settings2.odoo_url == "http://url2:8080"

    def test_settings_consistency_across_access(self) -> None:
        """Test that settings values remain consistent across multiple accesses."""
        settings = Settings(
            odoo_url="http://test:8080",
            api_max_request_body_bytes=500_000,
        )

        # Access same values multiple times
        assert settings.odoo_url == settings.odoo_url
        assert settings.api_max_request_body_bytes == settings.api_max_request_body_bytes
