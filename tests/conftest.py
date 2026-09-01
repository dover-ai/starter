"""Общие фикстуры тестов.

Каждый тест выполняется на чистой базе SQLite в памяти — тесты независимы
и не требуют поднятого PostgreSQL.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Настройки окружения задаются до импорта приложения.
os.environ["DATABASE_URL"] = "sqlite://"
# Не короче 32 байт — требование RFC 7518 для HMAC-SHA256 (см. app/config.py).
os.environ["SECRET_KEY"] = "test-secret-key-32-bytes-minimum-length"
os.environ["ENVIRONMENT"] = "local"

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # одно соединение на тест: база в памяти не исчезает между запросами
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    """Клиент API с подменённой сессией БД."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_credentials() -> dict[str, str]:
    return {"email": "user@example.com", "password": "correct-horse-battery"}


@pytest.fixture
def auth_headers(client, user_credentials) -> dict[str, str]:
    """Регистрирует пользователя и возвращает заголовок с токеном."""
    client.post("/auth/register", json=user_credentials)
    response = client.post(
        "/auth/token",
        data={"username": user_credentials["email"], "password": user_credentials["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
