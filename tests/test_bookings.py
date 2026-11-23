from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import auth_headers, slot


def book(client, headers, shop, start):
    return client.post(
        "/bookings",
        json={"barber_id": shop["barber_id"], "service_id": shop["service_id"], "starts_at": start},
        headers=headers,
    )


def test_booking_created(client, user_headers, shop):
    r = book(client, user_headers, shop, slot(10, 0))
    assert r.status_code == 201
    assert r.json()["status"] == "confirmed"


def test_overlapping_booking_is_409(client, user_headers, user2_headers, shop):
    assert book(client, user_headers, shop, slot(10, 0)).status_code == 201
    # другой клиент, пересекающееся время (10:15 попадает в 10:00-10:30)
    assert book(client, user2_headers, shop, slot(10, 15)).status_code == 409


def test_adjacent_booking_is_allowed(client, user_headers, user2_headers, shop):
    assert book(client, user_headers, shop, slot(10, 0)).status_code == 201
    # 10:30 начинается ровно тогда, когда заканчивается предыдущая
    assert book(client, user2_headers, shop, slot(10, 30)).status_code == 201


def test_cancel_frees_the_slot(client, user_headers, user2_headers, shop):
    first = book(client, user_headers, shop, slot(10, 0)).json()
    client.post(f"/bookings/{first['id']}/cancel", headers=user_headers)
    assert book(client, user2_headers, shop, slot(10, 0)).status_code == 201


def test_cannot_cancel_foreign_booking(client, user_headers, user2_headers, shop):
    first = book(client, user_headers, shop, slot(10, 0)).json()
    r = client.post(f"/bookings/{first['id']}/cancel", headers=user2_headers)
    assert r.status_code == 404


def test_cannot_book_in_the_past(client, user_headers, shop):
    r = book(client, user_headers, shop, slot(10, 0, days=-1))
    assert r.status_code == 400


def test_barber_must_provide_service(client, admin_headers, user_headers, shop):
    other = client.post(
        "/services",
        json={"name": "Борода", "duration_minutes": 20, "price": 10},
        headers=admin_headers,
    ).json()
    r = client.post(
        "/bookings",
        json={"barber_id": shop["barber_id"], "service_id": other["id"], "starts_at": slot()},
        headers=user_headers,
    )
    assert r.status_code == 400


def test_booking_requires_login(client, shop):
    r = client.post(
        "/bookings",
        json={"barber_id": shop["barber_id"], "service_id": shop["service_id"], "starts_at": slot()},
    )
    assert r.status_code == 401


def test_simultaneous_booking_only_one_wins(client, shop):
    """Пять человек одновременно жмут «записаться» на одно время."""
    start = slot(12, 0)
    all_headers = [auth_headers(client, f"racer{i}@mail.com") for i in range(5)]

    def attempt(headers):
        with TestClient(app) as c:
            return book(c, headers, shop, start).status_code

    with ThreadPoolExecutor(max_workers=5) as pool:
        codes = list(pool.map(attempt, all_headers))

    assert codes.count(201) == 1
    assert codes.count(409) == 4