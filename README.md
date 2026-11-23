# ✂️ Barbershop API

REST API для онлайн-записи в барбершоп. Клиенты выбирают мастера, услугу и время, а система гарантирует, что **один слот не может занять двое**: защита от двойного бронирования работает на уровне базы данных и выдерживает одновременные запросы.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)

---

## Возможности

- **Регистрация и вход** по email и паролю, авторизация через JWT
- **Роли**: `client` и `admin`. Мастеров и услуги создаёт только админ
- **Мастера и услуги**: у каждого мастера свой список услуг (связь многие ко многим)
- **Запись на время**: длительность берётся из услуги, конец записи считает сервер
- **Защита от двойной записи**: Postgres exclusion constraint запрещает пересекающиеся интервалы у одного мастера
- **Свободные слоты** мастера на выбранный день
- **Отмена записи**: запись не удаляется, а получает статус `cancelled`, слот сразу освобождается
- **Мягкое удаление мастера**: деактивация вместо удаления, история записей сохраняется
- **Тесты на pytest** с отдельной базой, включая проверку одновременных запросов

---

## Стек

| Назначение | Технология |
|---|---|
| Веб-фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Миграции | Alembic |
| База данных | PostgreSQL 16 |
| Валидация и настройки | Pydantic, pydantic-settings |
| Авторизация | JWT (PyJWT), хеширование паролей Argon2 (pwdlib) |
| Окружение | Docker, Docker Compose |
| Тесты | pytest, httpx |

---

## Быстрый старт

### Что нужно

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (или Docker + Docker Compose)
- Git

### 1. Клонировать репозиторий

```bash
git clone <ссылка-на-репозиторий>
cd BarbershopApi
```

### 2. Создать файл `.env`

Создай в корне проекта файл `.env`:

```env
POSTGRES_USER=barber
POSTGRES_PASSWORD=barber
POSTGRES_DB=barbershop
DATABASE_URL=postgresql+psycopg://barber:barber@db:5432/barbershop

SECRET_KEY=замени-на-длинную-случайную-строку
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Сгенерировать секретный ключ:

```bash
docker compose run --rm api python -c "import secrets; print(secrets.token_hex(32))"
```

> ⚠️ Файл `.env` содержит секреты и не должен попадать в git (он уже в `.gitignore`).

### 3. Запустить проект

```bash
docker compose up --build -d
```

Поднимутся два контейнера: `db` (PostgreSQL) и `api` (FastAPI).

### 4. Применить миграции

```bash
docker compose run --rm api alembic upgrade head
```

Это создаст таблицы и правило, запрещающее пересекающиеся записи.

### 5. Открыть

| Адрес | Что там |
|---|---|
| http://localhost:8000/docs | интерактивная документация Swagger |
| http://localhost:8000/health | проверка, что API и база живы |

---

## Первый администратор

Через API сделать себя админом нельзя (так задумано). Зарегистрируйся через `POST /auth/register`, затем один раз повысь роль в базе:

```bash
docker compose exec db psql -U barber -d barbershop -c "UPDATE users SET role = 'admin' WHERE email = 'you@mail.com';"
```

Роль читается из базы на каждом запросе, поэтому перелогиниваться не нужно.

---

## Как пользоваться (через Swagger)

1. `POST /auth/register`: создать пользователя
2. Нажать **Authorize**, ввести email (в поле `username`) и пароль
3. Под админом: создать мастера (`POST /barbers`) и услугу (`POST /services`)
4. Привязать услугу к мастеру: `PUT /barbers/{id}/services/{service_id}`
5. Посмотреть свободное время: `GET /barbers/{id}/slots?date=2026-12-01&service_id=1`
6. Записаться: `POST /bookings`

```json
{
  "barber_id": 1,
  "service_id": 1,
  "starts_at": "2026-12-01T10:00:00+05:00"
}
```

Время обязательно указывается **с часовым поясом**.

---

## Эндпоинты

### Авторизация

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| POST | `/auth/register` | все | регистрация |
| POST | `/auth/login` | все | получить токен (форма `username` + `password`) |
| GET | `/users/me` | клиент | данные текущего пользователя |

### Мастера

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| GET | `/barbers` | все | список активных мастеров |
| GET | `/barbers/{id}` | все | один мастер |
| POST | `/barbers` | админ | создать мастера |
| PATCH | `/barbers/{id}` | админ | изменить (в том числе `is_active`) |
| DELETE | `/barbers/{id}` | админ | деактивировать мастера |
| GET | `/barbers/{id}/slots?date=&service_id=` | все | свободные слоты на день |
| GET | `/barbers/{id}/services` | все | услуги мастера |
| PUT | `/barbers/{id}/services/{service_id}` | админ | назначить услугу мастеру |
| DELETE | `/barbers/{id}/services/{service_id}` | админ | снять услугу с мастера |

### Услуги

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| GET | `/services` | все | список услуг |
| GET | `/services/{id}` | все | одна услуга |
| POST | `/services` | админ | создать услугу |
| PATCH | `/services/{id}` | админ | изменить услугу |
| DELETE | `/services/{id}` | админ | удалить услугу |

### Записи

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| POST | `/bookings` | клиент | создать запись |
| GET | `/bookings/my` | клиент | мои записи |
| POST | `/bookings/{id}/cancel` | клиент | отменить свою запись |

### Коды ответов

| Код | Значение |
|---|---|
| 400 | неверный запрос (например, запись в прошлое или мастер не делает услугу) |
| 401 | нет токена или он недействителен |
| 403 | недостаточно прав |
| 404 | объект не найден |
| 409 | конфликт (email занят или слот уже занят) |
| 422 | данные не прошли валидацию |

---

## Как работает защита от двойной записи

Проверки «свободно ли» в коде недостаточно: при двух одновременных запросах оба могут увидеть свободный слот и оба создать запись. Поэтому правило хранится **в самой базе** и применяется миграцией:

```sql
ALTER TABLE bookings
ADD CONSTRAINT no_overlapping_bookings
EXCLUDE USING gist (
    barber_id WITH =,
    tstzrange(starts_at, ends_at) WITH &&
) WHERE (status = 'confirmed');
```

Читается так: у одного мастера не может быть двух подтверждённых записей с пересекающимся временем. Когда база отклоняет вставку, API ловит `IntegrityError` и отвечает `409`. Отменённые записи правило не учитывает, поэтому слот освобождается сразу после отмены. Соседние записи встык (10:00-10:30 и 10:30-11:00) разрешены.

---

## Структура проекта

```
BarbershopApi/
├── app/
│   ├── main.py              # создание приложения, подключение роутеров
│   ├── core/
│   │   ├── config.py        # настройки из переменных окружения
│   │   └── security.py      # хеш паролей, создание и проверка JWT
│   ├── db/
│   │   ├── base.py          # базовый класс моделей
│   │   └── session.py       # engine, сессии, зависимость get_db
│   ├── models/              # таблицы БД (SQLAlchemy)
│   │   ├── user.py
│   │   ├── barber.py
│   │   ├── service.py
│   │   ├── booking.py
│   │   └── associations.py  # таблица barber_services
│   ├── schemas/             # форматы запросов и ответов (Pydantic)
│   └── routers/             # эндпоинты
│       ├── auth.py
│       ├── barbers.py
│       ├── services.py
│       ├── bookings.py
│       └── deps.py          # get_current_user, get_current_admin
├── migrations/              # миграции Alembic
├── tests/                   # тесты pytest
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

### Модель данных

```
users ──< bookings >── barbers
              │            │
              ▼            │ (многие ко многим)
          services >── barber_services ──< barbers
```

---

## Работа с миграциями

```bash
# создать миграцию по изменениям в моделях
docker compose run --rm api alembic revision --autogenerate -m "описание"

# применить все миграции
docker compose run --rm api alembic upgrade head

# откатить последнюю
docker compose run --rm api alembic downgrade -1

# текущая версия базы
docker compose run --rm api alembic current
```

Всегда открывай сгенерированный файл и проверяй его перед применением. Правило против пересечений Alembic сам не создаёт, оно добавлено в миграцию вручную.

---

## Тесты

Тесты работают с **отдельной базой** `barbershop_test`, рабочие данные не затрагиваются. Таблицы в ней создаются теми же миграциями, поэтому защита от пересечений тоже проверяется.

Один раз создай тестовую базу:

```bash
docker compose exec db psql -U barber -d barbershop -c "CREATE DATABASE barbershop_test;"
```

Запуск:

```bash
docker compose run --rm api pytest -v
```

Что проверяется:

- права доступа (`401`, `403`, роль нельзя задать при регистрации)
- создание записи, пересечения, соседние слоты
- отмена освобождает слот, чужую запись отменить нельзя
- запрет записи в прошлое
- мастер должен делать выбранную услугу
- пять одновременных запросов на один слот: успешен ровно один

---

## Полезные команды Docker

| Команда | Что делает |
|---|---|
| `docker compose up -d` | запустить в фоне |
| `docker compose up --build -d` | пересобрать образ и запустить (после изменения `requirements.txt`) |
| `docker compose logs -f api` | смотреть логи API |
| `docker compose down` | остановить контейнеры (данные базы сохраняются) |
| `docker compose down -v` | остановить и **удалить данные базы** |
| `docker compose exec db psql -U barber -d barbershop` | консоль PostgreSQL |

Код смонтирован в контейнер, поэтому при правках файлов сервер перезапускается сам (`--reload`), пересборка не нужна.

---

## Решение типичных проблем

| Проблема | Решение |
|---|---|
| `failed to connect to the docker API` | запусти Docker Desktop и дождись статуса Engine running |
| Порт 5432 занят | в `docker-compose.yml` замени `"5432:5432"` на `"5433:5432"` |
| Приложение не стартует и пишет про `secret_key` | добавь `SECRET_KEY` в `.env` |
| `ModuleNotFoundError` после добавления библиотеки | `docker compose up --build -d` |
| Поменял пароль в `.env`, а база не реагирует | пароль применяется только при первой инициализации тома: `docker compose down -v` (сотрёт данные) |

---

