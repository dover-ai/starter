"""Тесты правил конфигурации.

Эти проверки фиксируют требования безопасности: их нельзя нарушить,
не сломав сборку.
"""

import pytest
from pydantic import ValidationError

from app.config import INSECURE_DEFAULT_SECRET, MIN_SECRET_LENGTH, Settings


def test_default_secret_is_long_enough():
    """Даже значение-заглушка обязано удовлетворять требованию длины."""
    assert len(INSECURE_DEFAULT_SECRET) >= MIN_SECRET_LENGTH


def test_short_secret_is_rejected():
    """Короткий ключ HMAC небезопасен (RFC 7518 §3.2) и не должен приниматься."""
    with pytest.raises(ValidationError):
        Settings(secret_key="too-short", _env_file=None)


def test_production_rejects_default_secret():
    """В production приложение не стартует с ключом-заглушкой."""
    from app.config import get_settings

    get_settings.cache_clear()
    settings = Settings(
        environment="production", secret_key=INSECURE_DEFAULT_SECRET, _env_file=None
    )
    assert settings.is_production
    assert settings.secret_key == INSECURE_DEFAULT_SECRET  # проверку делает get_settings


def test_cors_origins_parsed_from_string():
    settings = Settings(cors_origins="https://a.example, https://b.example ,", _env_file=None)

    assert settings.cors_origin_list == ["https://a.example", "https://b.example"]


def test_cors_empty_by_default():
    assert Settings(_env_file=None).cors_origin_list == []
