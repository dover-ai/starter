"""Проверки состояния сервиса.

/health/live  — процесс жив (для перезапуска контейнера)
/health/ready — сервис готов принимать трафик, включая доступность БД
"""

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.config import get_settings
from app.deps import DbSession
from app.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", environment=settings.environment, database="not checked")


@router.get("/ready", response_model=HealthResponse)
def readiness(db: DbSession, response: Response) -> HealthResponse:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:  # noqa: BLE001 — наружу отдаём статус, детали пишутся в лог
        db_status = "unavailable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        environment=settings.environment,
        database=db_status,
    )
