USER = {"name": "Ada", "email": "ada@example.com", "password": "s3cret"}


def register(client):
    return client.post("/auth/register", json=USER)


def login(client, password=USER["password"]):
    return client.post("/auth/login", params={"email": USER["email"], "password": password})


def test_register_login_me(client):
    assert register(client).status_code == 200

    response = login(client)
    assert response.status_code == 200
    token = response.json()["token"]

    me = client.get("/auth/me", params={"token": token})
    assert me.status_code == 200
    assert me.json()["user"]


def test_duplicate_register_rejected(client):
    register(client)
    assert register(client).status_code == 401


def test_wrong_password_rejected(client):
    register(client)
    assert login(client, password="wrong").status_code == 401


def test_invalid_token_rejected(client):
    assert client.get("/auth/me", params={"token": "garbage"}).status_code == 401
