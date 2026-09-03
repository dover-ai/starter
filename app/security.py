"""Хеширование паролей и работа с JWT."""

from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
import jwt

from app.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Пароль хешируется bcrypt с индивидуальной солью."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Сравнение выполняется в постоянном времени — защита от timing-атак."""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        # Некорректный хеш в базе не должен ронять приложение.
        return False


@lru_cache(maxsize=1)
def warm_placeholder_hash() -> str:
    """Хеш-заглушка для выравнивания времени. Считается один раз за процесс.

    Вызывается при старте приложения, чтобы первый запрос с незнакомым адресом
    не отличался по времени от последующих.
    """
    return hash_password("timing-equalization-placeholder")


def verify_password_or_equalize(password: str, password_hash: str | None) -> bool:
    """Проверка пароля, не выдающая существование учётной записи временем ответа.

    Если хеша нет — пользователь не найден — проверка всё равно выполняется,
    против заглушки. Без этого ответ возвращается мгновенно, а для существующего
    адреса тратится время bcrypt: разница в десятки раз позволяет перебором
    определить, какие адреса зарегистрированы.
    """
    if password_hash is None:
        verify_password(password, warm_placeholder_hash())
        return False
    return verify_password(password, password_hash)


def create_access_token(subject: str, ttl: timedelta | None = None) -> str:
    settings = get_settings()
    expire_delta = ttl or timedelta(minutes=settings.access_token_ttl_minutes)
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expire_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Возвращает subject токена или None, если токен недействителен или истёк."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
