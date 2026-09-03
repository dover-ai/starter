"""Тесты защит, добавленных по результатам аудита.

Каждый тест закрывает конкретную находку. Их назначение — не дать
исправлению незаметно откатиться: без такого теста защита исчезает
при первом же рефакторинге, и никто этого не замечает.
"""

import time

from app.security import hash_password, verify_password_or_equalize

# Порог для проверки того, что bcrypt действительно отработал.
# Реальная проверка занимает ~200 мс, мгновенный возврат — доли миллисекунды;
# 20 мс надёжно отделяет одно от другого и не зависит от мощности машины.
BCRYPT_WORK_THRESHOLD_MS = 20


def _elapsed_ms(fn) -> float:
    started = time.perf_counter()
    fn()
    return (time.perf_counter() - started) * 1000


def test_unknown_user_still_costs_bcrypt_time():
    """Отсутствие пользователя не должно определяться по времени ответа.

    Находка аудита: без выравнивания несуществующий адрес отвечал за 3 мс,
    существующий — за 195 мс. Разница в 61 раз позволяла перебором
    выяснить, какие адреса зарегистрированы.
    """
    elapsed = _elapsed_ms(lambda: verify_password_or_equalize("any-password", None))

    assert elapsed >= BCRYPT_WORK_THRESHOLD_MS, (
        f"проверка заняла {elapsed:.1f} мс — bcrypt не выполнялся, "
        "значит отсутствие учётной записи снова выдаёт себя временем ответа"
    )


def test_equalized_check_reports_failure():
    """Выравнивание времени не должно превращаться в пропуск проверки."""
    assert verify_password_or_equalize("any-password", None) is False


def test_correct_password_still_accepted():
    """Основная функция проверки не сломана выравниванием."""
    stored = hash_password("correct-horse-battery")

    assert verify_password_or_equalize("correct-horse-battery", stored) is True
    assert verify_password_or_equalize("wrong-password", stored) is False


def test_timing_gap_between_known_and_unknown_is_small():
    """Время ответа для существующего и несуществующего адреса сопоставимо."""
    stored = hash_password("correct-horse-battery")

    known = _elapsed_ms(lambda: verify_password_or_equalize("wrong-password", stored))
    unknown = _elapsed_ms(lambda: verify_password_or_equalize("wrong-password", None))

    slower, faster = max(known, unknown), min(known, unknown)
    assert slower / faster < 3, (
        f"разница во времени {slower:.1f} мс против {faster:.1f} мс — "
        "существование учётной записи различимо по задержке"
    )


def test_login_answers_identically_for_unknown_and_wrong_password(client, user_credentials):
    """Ответ не должен отличаться ни кодом, ни телом."""
    client.post("/auth/register", json=user_credentials)

    wrong_password = client.post(
        "/auth/token",
        data={"username": user_credentials["email"], "password": "definitely-wrong"},
    )
    unknown_user = client.post(
        "/auth/token",
        data={"username": "ghost@example.com", "password": "definitely-wrong"},
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_security_headers_present(client):
    """Заголовки, ограничивающие поведение браузера, отдаются на каждом ответе."""
    response = client.get("/health/live")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_strict_headers_only_in_production(client):
    """HSTS и политика содержимого включаются только в production.

    В локальном окружении строгая политика сломала бы интерактивную
    документацию, которая в production и так закрыта.
    """
    response = client.get("/health/live")

    assert "Strict-Transport-Security" not in response.headers
    assert "Content-Security-Policy" not in response.headers
