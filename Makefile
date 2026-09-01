.PHONY: help install dev test lint fmt cov run up down build check

help:  ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

install:  ## Установить зависимости
	pip install -e ".[dev]" email-validator

test:  ## Прогнать тесты с покрытием
	pytest

lint:  ## Проверить код линтером
	ruff check .

fmt:  ## Отформатировать код
	ruff check --fix .
	ruff format .

cov:  ## Отчёт о покрытии в HTML
	pytest --cov=app --cov-report=html
	@echo "Отчёт: htmlcov/index.html"

run:  ## Запустить сервис локально
	uvicorn app.main:app --reload

up:  ## Поднять окружение в Docker
	docker compose up -d --build

down:  ## Остановить окружение
	docker compose down

build:  ## Собрать образ
	docker build -t doverai-starter .

check: lint test  ## Полная проверка перед коммитом
