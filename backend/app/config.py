from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str
    secret_key: str
    database_url: str = "sqlite:///./healthguide.db"
    environment: str = "development"
    allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000"
    model_name: str = "llama-3.3-70b-versatile"
    access_token_minutes: int = 60 * 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
