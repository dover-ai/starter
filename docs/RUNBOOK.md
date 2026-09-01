# Runbook

Инструкция для того, кто эксплуатирует сервис. Написана так, чтобы ей мог
воспользоваться инженер, не участвовавший в разработке.

## Запуск

```bash
cp .env.example .env
openssl rand -hex 32          # результат → SECRET_KEY в .env
docker compose up -d --build
```

Проверка:

```bash
curl http://localhost:8000/health/ready
# ожидаемо: {"status":"ok","environment":"local","database":"ok"}
```

## Остановка и перезапуск

```bash
docker compose restart api    # перезапустить только приложение
docker compose down           # остановить всё (данные сохраняются в томе)
docker compose down -v        # остановить и УДАЛИТЬ данные
```

## Проверки состояния

| Эндпоинт | Что означает | Действие при отказе |
|---|---|---|
| `/health/live` | Процесс жив | Не отвечает → перезапустить контейнер |
| `/health/ready` | Готов к трафику | 503 → проверить БД, трафик не слать |

Настройка оркестратора: `live` — на liveness-проверку, `ready` — на readiness.
Перезапускать контейнер при недоступности БД бессмысленно, поэтому проверки разделены.

## Логи

```bash
docker compose logs -f api           # поток логов
docker compose logs api | grep ERROR # только ошибки
```

Формат — JSON, каждая строка содержит время, уровень, сообщение.
В сообщении о запросе есть `request_id`, метод, путь, код ответа и время обработки.

**Поиск по конкретному запросу:** попросите у клиента заголовок `X-Request-ID`
из ответа и найдите его в логах:

```bash
docker compose logs api | grep "request_id=<значение>"
```

## Типовые проблемы

### Сервис не стартует, в логах `SECRET_KEY не задан в production`

Ожидаемое поведение: приложение отказывается работать с ключом-заглушкой.
Сгенерируйте ключ (`openssl rand -hex 32`) и задайте `SECRET_KEY`.

### `/health/ready` отдаёт 503, database: unavailable

1. Проверьте, поднята ли БД: `docker compose ps`
2. Логи БД: `docker compose logs db`
3. Проверьте `DATABASE_URL` — хост внутри compose должен быть `db`, а не `localhost`
4. Проверьте доступность: `docker compose exec db pg_isready -U postgres`

### Все запросы возвращают 401

- Истёк токен (по умолчанию 60 минут) — получите новый через `/auth/token`
- Изменился `SECRET_KEY` — все ранее выданные токены стали недействительны
- Проверьте формат заголовка: `Authorization: Bearer <токен>`

### Медленные ответы

1. Найдите долгие запросы в логах — время обработки указано в каждой строке
2. Проверьте нагрузку на БД: `docker stats`
3. При росте объёма данных проверьте индексы — в шаблоне проиндексированы
   `users.email`, `items.title`, `items.owner_id`

## Резервное копирование

```bash
# Создать копию
docker compose exec db pg_dump -U postgres app > backup_$(date +%Y%m%d).sql

# Восстановить
cat backup_20260901.sql | docker compose exec -T db psql -U postgres app
```

⚠ Регулярность копий и их хранение вне сервера — зона ответственности эксплуатации.
Автоматизация в шаблон не входит (см. [TECH_DEBT.md](TECH_DEBT.md)).

## Откат

```bash
# Вернуться на предыдущий образ
docker compose down
docker tag doverai-starter:<предыдущий-sha> doverai-starter:latest
docker compose up -d
```

Образы помечаются SHA коммита в CI — можно откатиться на любую сборку.

## Обновление зависимостей

```bash
pip list --outdated
# обновить версии в pyproject.toml
make check      # линтер + тесты должны пройти
docker build -t doverai-starter .
```

Обновлять по одной группе за раз: так проще понять, что сломалось.

## Контакты

| Ситуация | Куда |
|---|---|
| Вопросы по коду и архитектуре | команда разработки |
| Инциденты в проде | дежурный (заполнить на проекте) |
