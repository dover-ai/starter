"""Конфигурация приложения.

Все настройки читаются из переменных окружения — в коде нет ни одного секрета.
См. .env.example и docs/SECURITY.md.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Значение-заглушка для локальной разработки. В production запрещено (см. get_settings).
INSECURE_DEFAULT_SECRET = "dev-only-insecure-secret-change-me-before-deploy"  # noqa: S105

# RFC 7518 §3.2: для HMAC-SHA256 ключ должен быть не короче длины хеша, то есть 32 байта.
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DoverAI Starter"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = False

    # База данных. В тестах подменяется на SQLite (см. tests/conftest.py).
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/app"

    # Секрет для подписи JWT. Значение по умолчанию работает только локально:
    # в production приложение не стартует, пока не задан настоящий SECRET_KEY.
    secret_key: str = Field(default=INSECURE_DEFAULT_SECRET, min_length=MIN_SECRET_LENGTH)
    access_token_ttl_minutes: int = 60

    # CORS: список источников через запятую, пусто — запросы с других origin запрещены.
    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Настройки кешируются: файл окружения читается один раз за процесс."""
    settings = Settings()
    if settings.is_production and settings.secret_key == INSECURE_DEFAULT_SECRET:
        raise RuntimeError(
            "SECRET_KEY не задан в production. Установите переменную окружения SECRET_KEY."
        )
    return settings
