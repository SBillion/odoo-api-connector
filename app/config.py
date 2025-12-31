"""Configuration settings for the application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    odoo_url: str = "http://localhost:8069"
    odoo_db: str = "odoo"
    odoo_username: str = "admin"
    odoo_password: str = "admin"
    odoo_api_key: str | None = None

    api_enable_rate_limit: bool = True
    api_rate_limit_default: str = "60/minute"

    api_enable_security_headers: bool = True
    api_enable_max_body_size: bool = True
    api_max_request_body_bytes: int = 1_048_576

    # Note: for env var parsing, Pydantic expects JSON (e.g. '["*"]')
    api_cors_origins: list[str] = ["*"]
    api_allowed_hosts: list[str] = ["*"]


settings = Settings()
