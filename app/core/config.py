"""Centralized, validated configuration (12-factor app pattern).

Why this file exists:
- All settings come from environment variables / .env, never hardcoded.
- Pydantic validates types at startup (fail fast if misconfigured).
- `lru_cache` gives us a single shared Settings instance (simple DI).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "greenhouse-iot"
    app_env: str = "local"  # local | dev | prod
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # Wired in Step 1 (declared here now so .env.example stays in sync):
    # database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/greenhouse"


@lru_cache
def get_settings() -> Settings:
    return Settings()
