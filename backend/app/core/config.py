from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_url: str = Field(default="http://127.0.0.1:5173", alias="FRONTEND_URL")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./beacon.db", alias="DATABASE_URL"
    )

    # Keycloak / OIDC
    keycloak_url: str = Field(default="http://127.0.0.1:8080", alias="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="beacon", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="beacon-studio", alias="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: str = Field(default="", alias="KEYCLOAK_CLIENT_SECRET")
    keycloak_admin_user: str = Field(default="admin", alias="KEYCLOAK_ADMIN_USER")
    keycloak_admin_password: str = Field(default="", alias="KEYCLOAK_ADMIN_PASSWORD")
    oidc_issuer: str = Field(
        default="http://127.0.0.1:8080/realms/beacon", alias="OIDC_ISSUER"
    )
    oidc_audience: str = Field(default="beacon-studio", alias="OIDC_AUDIENCE")

    # LLM Providers (optional)
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_provider: str = Field(default="openai-compatible", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")

    # Security
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    csrf_secret_key: str = Field(default="change-me-in-production", alias="CSRF_SECRET_KEY")

    # Demo mode
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_demo_mode(self) -> bool:
        return self.demo_mode and self.is_development


@lru_cache
def get_settings() -> Settings:
    return Settings()