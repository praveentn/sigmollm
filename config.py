from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SigmoLLM"
    secret_key: str = "change-me-to-a-random-64-char-secret-string-in-production"
    admin_password: str = "changeme"
    admin_api_key: str = "admin-api-key-changeme"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sigmollm"

    ollama_url: str = "http://localhost:11434"
    default_model: str = "gemma4:e2b"

    default_rpm: int = 60
    default_rpd: int = 1000

    jwt_expire_hours: int = 24
    cookie_name: str = "sigmollm_session"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
