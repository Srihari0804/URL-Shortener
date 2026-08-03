VALID_USER_PAYLOAD = {
    "email": "testuser@gmail.com",
    "password": "password123"
}

def test_create_users(client):
    response = client.post("/users/signup", json=VALID_USER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == VALID_USER_PAYLOAD["email"]
    assert "api_key" in data


def test_create_user_duplicate_email(client):
    # First creation
    client.post("/users/signup", json=VALID_USER_PAYLOAD)

    # Second creation attempt
    response = client.post("/users/signup", json=VALID_USER_PAYLOAD)
    assert response.status_code == 409


def test_regenerate_api_key_success(client):
    setup_res = client.post("/users/signup", json=VALID_USER_PAYLOAD)
    original_api_key = setup_res.json()["api_key"]

    # Regenerate the key
    response = client.post("/users/regenerate-key", json=VALID_USER_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == VALID_USER_PAYLOAD["email"]
    assert "api_key" in data
    assert data["api_key"] != original_api_key


def test_regenerate_api_key_invalid_email(client):
    invalid_payload = {"email": "dummy@gmail.com", "password": "password123"}
    response = client.post("/users/regenerate-key", json=invalid_payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_regenerate_api_key_invalid_password(client):
    client.post("/users/signup", json=VALID_USER_PAYLOAD)

    invalid_payload = {
        "email": VALID_USER_PAYLOAD["email"],
        "password": "wrong_password"
    }
    response = client.post("/users/regenerate-key", json=invalid_payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_delete_user_success(client):
    # Create user
    setup_res = client.post("/users/signup", json=VALID_USER_PAYLOAD)
    api_key = setup_res.json()["api_key"]

    # Delete user
    response = client.delete("/users/me", headers={"API-Key": api_key})
    assert response.status_code == 204

    # Verify user is actually deleted
    regen_res = client.post("/users/regenerate-key", json=VALID_USER_PAYLOAD)
    assert regen_res.status_code == 401

def test_delete_user_invalid_api_key(client):
    response = client.delete("/users/me", headers={"API-Key": "fake-api-key"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API-Key"

def test_delete_user_empty_api_key(client):
    response = client.delete("/users/me", headers={"API-Key": ""})
    assert response.status_code == 401

def test_delete_user_missing_api_key_header(client):
    response = client.delete("/users/me")
    assert response.status_code == 401


def test_get_user_success(client):
    # Create user
    setup_res = client.post("/users/signup", json=VALID_USER_PAYLOAD)
    api_key = setup_res.json()["api_key"]

    # Get user
    response = client.get("/users/me", headers={"API-Key": api_key})
    assert response.status_code == 200
    assert response.json()["email"] == VALID_USER_PAYLOAD["email"]


def test_get_user_invalid_api_key(client):
    response = client.get("/users/me", headers={"API-Key": "bad-api-key"})
    assert response.status_code == 401
