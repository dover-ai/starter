"""Тесты CRUD и, главное, изоляции данных между пользователями."""


def _make_second_user_headers(client) -> dict[str, str]:
    other = {"email": "other@example.com", "password": "another-strong-pass"}
    client.post("/auth/register", json=other)
    token = client.post(
        "/auth/token", data={"username": other["email"], "password": other["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_read_item(client, auth_headers):
    created = client.post("/items", json={"title": "Первая задача"}, headers=auth_headers)
    assert created.status_code == 201
    item_id = created.json()["id"]

    fetched = client.get(f"/items/{item_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Первая задача"


def test_items_require_auth(client):
    assert client.get("/items").status_code == 401
    assert client.post("/items", json={"title": "x"}).status_code == 401


def test_list_returns_only_own_items(client, auth_headers):
    client.post("/items", json={"title": "Моя запись"}, headers=auth_headers)
    other_headers = _make_second_user_headers(client)
    client.post("/items", json={"title": "Чужая запись"}, headers=other_headers)

    response = client.get("/items", headers=auth_headers)

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert titles == ["Моя запись"]


def test_cannot_read_foreign_item(client, auth_headers):
    """Доступ по прямому идентификатору к чужой записи должен давать 404."""
    other_headers = _make_second_user_headers(client)
    foreign_id = client.post(
        "/items", json={"title": "Чужая запись"}, headers=other_headers
    ).json()["id"]

    response = client.get(f"/items/{foreign_id}", headers=auth_headers)

    assert response.status_code == 404


def test_cannot_update_or_delete_foreign_item(client, auth_headers):
    other_headers = _make_second_user_headers(client)
    foreign_id = client.post(
        "/items", json={"title": "Чужая запись"}, headers=other_headers
    ).json()["id"]

    assert client.patch(
        f"/items/{foreign_id}", json={"title": "Взлом"}, headers=auth_headers
    ).status_code == 404
    assert client.delete(f"/items/{foreign_id}", headers=auth_headers).status_code == 404

    # Запись владельца осталась нетронутой.
    still_there = client.get(f"/items/{foreign_id}", headers=other_headers)
    assert still_there.status_code == 200
    assert still_there.json()["title"] == "Чужая запись"


def test_update_item(client, auth_headers):
    item_id = client.post("/items", json={"title": "Было"}, headers=auth_headers).json()["id"]

    response = client.patch(f"/items/{item_id}", json={"title": "Стало"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["title"] == "Стало"


def test_delete_item(client, auth_headers):
    created = client.post("/items", json={"title": "На удаление"}, headers=auth_headers)
    item_id = created.json()["id"]

    assert client.delete(f"/items/{item_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/items/{item_id}", headers=auth_headers).status_code == 404


def test_create_rejects_empty_title(client, auth_headers):
    response = client.post("/items", json={"title": ""}, headers=auth_headers)

    assert response.status_code == 422


def test_list_pagination_bounds(client, auth_headers):
    assert client.get("/items?limit=0", headers=auth_headers).status_code == 422
    assert client.get("/items?limit=101", headers=auth_headers).status_code == 422
    assert client.get("/items?offset=-1", headers=auth_headers).status_code == 422
