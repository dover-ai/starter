"""Тесты регистрации и аутентификации — критический путь."""

import pytest


def test_register_creates_user(client, user_credentials):
    response = client.post("/auth/register", json=user_credentials)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == user_credentials["email"]
    assert body["is_active"] is True
    # Пароль и его хеш не должны попадать в ответ ни при каких условиях.
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client, user_credentials):
    client.post("/auth/register", json=user_credentials)
    response = client.post("/auth/register", json=user_credentials)

    assert response.status_code == 409


@pytest.mark.parametrize("password", ["short", "1234567"])
def test_register_rejects_weak_password(client, password):
    response = client.post("/auth/register", json={"email": "a@example.com", "password": password})

    assert response.status_code == 422


def test_register_rejects_invalid_email(client):
    payload = {"email": "not-an-email", "password": "longenough"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_login_returns_token(client, user_credentials):
    client.post("/auth/register", json=user_credentials)

    response = client.post(
        "/auth/token",
        data={"username": user_credentials["email"], "password": user_credentials["password"]},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client, user_credentials):
    client.post("/auth/register", json=user_credentials)

    response = client.post(
        "/auth/token",
        data={"username": user_credentials["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_unknown_user_matches_wrong_password_response(client, user_credentials):
    """Ответы должны совпадать, иначе по ним можно перебирать существующие адреса."""
    client.post("/auth/register", json=user_credentials)

    wrong_password = client.post(
        "/auth/token",
        data={"username": user_credentials["email"], "password": "wrong-password"},
    )
    unknown_user = client.post(
        "/auth/token",
        data={"username": "nobody@example.com", "password": "wrong-password"},
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_me_requires_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_rejects_garbage_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers, user_credentials):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == user_credentials["email"]
