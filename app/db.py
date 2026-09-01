"""Подключение к базе данных и сессии SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Базовый класс моделей."""


def _make_engine():
    settings = get_settings()
    # SQLite (используется в тестах) требует отдельного флага для многопоточности.
    is_sqlite = settings.database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,  # переподключение после разрыва соединения
        echo=settings.debug,
    )


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Зависимость FastAPI: сессия на запрос, всегда закрывается."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
