# Многоэтапная сборка: в финальный образ не попадают инструменты сборки.
FROM python:3.12-slim AS builder

WORKDIR /build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install \
    "fastapi>=0.115" "uvicorn[standard]>=0.30" "sqlalchemy>=2.0" "psycopg[binary]>=3.2" \
    "pydantic>=2.9" "pydantic-settings>=2.5" "pyjwt>=2.9" "bcrypt>=4.2" \
    "python-multipart>=0.0.12" "email-validator>=2.0"


FROM python:3.12-slim

# Приложение работает не от root — базовое требование к production-образу.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/usr/local/bin:$PATH"

COPY --from=builder /install /usr/local
COPY app ./app

USER appuser
EXPOSE 8000

# Проверка живости на уровне образа: оркестратор сам перезапустит зависший контейнер.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health/live', timeout=2).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
