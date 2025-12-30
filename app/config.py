"""Configuration settings for the application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    odoo_url: str = "http://localhost:8069"
    odoo_db: str = "odoo"
    odoo_username: str = "admin"
    odoo_password: str = "admin"


settings = Settings()
