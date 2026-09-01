"""Проверки состояния и служебных эндпоинтов."""


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "service" in response.json()


def test_liveness(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_reports_database(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_request_id_header_is_returned(client):
    response = client.get("/health/live", headers={"X-Request-ID": "test-request-id"})

    assert response.headers["X-Request-ID"] == "test-request-id"


def test_request_id_generated_when_absent(client):
    response = client.get("/health/live")

    assert response.headers.get("X-Request-ID")
