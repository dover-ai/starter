"""Схемы запросов и ответов (Pydantic).

Схемы отделены от моделей БД намеренно: наружу отдаётся только то,
что перечислено явно. Хеш пароля физически не может попасть в ответ.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def normalize_email(value: str) -> str:
    """Приводит адрес к единому виду.

    Формально локальная часть адреса регистрозависима (RFC 5321 §2.4), но на
    практике почтовые системы её регистр игнорируют. Если хранить адреса как
    введено, `user@example.com` и `USER@example.com` становятся разными
    учётными записями: появляется двойник существующего адреса, а владелец
    не может войти, набрав свой адрес в другом регистре.
    """
    return value.strip().lower()


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return normalize_email(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 — тип токена по OAuth2, не секрет


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    owner_id: int
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: str
