def test_create_barber_without_token_is_401(client):
    r = client.post("/barbers", json={"name": "X"})
    assert r.status_code == 401


def test_create_barber_as_client_is_403(client, user_headers):
    r = client.post("/barbers", json={"name": "X"}, headers=user_headers)
    assert r.status_code == 403


def test_create_barber_as_admin_is_201(client, admin_headers):
    r = client.post("/barbers", json={"name": "X"}, headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["name"] == "X"


def test_list_barbers_is_public(client):
    r = client.get("/barbers")
    assert r.status_code == 200


def test_register_ignores_role_field(client):
    client.post(
        "/auth/register",
        json={"email": "hacker@mail.com", "password": "password123",
              "full_name": "H", "role": "admin"},
    )
    r = client.post("/auth/login", data={"username": "hacker@mail.com", "password": "password123"})
    token = r.json()["access_token"]
    me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "client"