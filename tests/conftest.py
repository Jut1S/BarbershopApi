import os


os.environ["DATABASE_URL"] = (
    os.environ["DATABASE_URL"].rsplit("/", 1)[0] + "/barbershop_test"
)

from datetime import datetime, timedelta, timezone  # noqa: E402

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.main import app
from app.models import User, UserRole


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
def clean_db():
    """Перед каждым тестом очищаем все таблицы."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE users, barbers, services, bookings, barber_services "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(client: TestClient, email: str, password: str = "password123"):
    """Регистрирует пользователя, логинит, возвращает заголовок с токеном."""
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    r = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def user_headers(client):
    return auth_headers(client, "user1@mail.com")


@pytest.fixture
def user2_headers(client):
    return auth_headers(client, "user2@mail.com")


@pytest.fixture
def admin_headers(client):
    headers = auth_headers(client, "admin@mail.com")
    with SessionLocal() as db:
        admin = db.query(User).filter(User.email == "admin@mail.com").one()
        admin.role = UserRole.admin
        db.commit()
    return headers


@pytest.fixture
def shop(client, admin_headers):
    """Мастер + услуга на 30 минут, уже связанные между собой."""
    barber = client.post("/barbers", json={"name": "Алексей"}, headers=admin_headers).json()
    service = client.post(
        "/services",
        json={"name": "Стрижка", "duration_minutes": 30, "price": 15},
        headers=admin_headers,
    ).json()
    client.put(
        f"/barbers/{barber['id']}/services/{service['id']}", headers=admin_headers
    )
    return {"barber_id": barber["id"], "service_id": service["id"]}


def slot(hour: int = 10, minute: int = 0, days: int = 2) -> str:
    """Время в будущем (через `days` дней) в виде строки ISO."""
    t = datetime.now(timezone.utc) + timedelta(days=days)
    return t.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()