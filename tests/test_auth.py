from datetime import timedelta
import uuid
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.anyio
async def test_successful_signup(client: AsyncClient):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Test User",
        "email": email,
        "password": "strongPassword123!",
    }
    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == email.lower()
    assert "id" in data
    # Password and hash must NOT be exposed
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.anyio
async def test_duplicate_email(client: AsyncClient):
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Duplicate User",
        "email": email,
        "password": "password123",
    }
    # First signup
    res1 = await client.post("/auth/signup", json=payload)
    assert res1.status_code == 201

    # Second signup with same email
    res2 = await client.post("/auth/signup", json=payload)
    assert res2.status_code == 409
    assert res2.json()["detail"] == "Email already registered"


@pytest.mark.anyio
async def test_successful_login(client: AsyncClient):
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    password = "correct_password"
    signup_payload = {
        "name": "Login User",
        "email": email,
        "password": password,
    }
    res_signup = await client.post("/auth/signup", json=signup_payload)
    assert res_signup.status_code == 201

    # Valid login
    login_payload = {
        "email": email,
        "password": password,
    }
    res_login = await client.post("/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert len(token_data["access_token"]) > 20


@pytest.mark.anyio
async def test_wrong_password(client: AsyncClient):
    email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
    signup_payload = {
        "name": "Wrong PW User",
        "email": email,
        "password": "correct_password",
    }
    res_signup = await client.post("/auth/signup", json=signup_payload)
    assert res_signup.status_code == 201

    # Wrong password
    login_payload = {
        "email": email,
        "password": "incorrect_password",
    }
    res_login = await client.post("/auth/login", json=login_payload)
    assert res_login.status_code == 401
    assert res_login.json()["detail"] == "Invalid email or password"


@pytest.mark.anyio
async def test_auth_me_without_token(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


@pytest.mark.anyio
async def test_auth_me_with_valid_token(client: AsyncClient):
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    password = "userPassword123"
    signup_payload = {
        "name": "Abhishek",
        "email": email,
        "password": password,
    }
    res_signup = await client.post("/auth/signup", json=signup_payload)
    assert res_signup.status_code == 201

    # Login to get token
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]

    # Access /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["name"] == "Abhishek"
    assert me_data["email"] == email.lower()
    assert "id" in me_data
    assert "password" not in me_data
    assert "hashed_password" not in me_data


@pytest.mark.anyio
async def test_auth_me_with_invalid_token(client: AsyncClient):
    headers = {"Authorization": "Bearer invalid.token.value"}
    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.anyio
async def test_auth_me_with_expired_token(client: AsyncClient):
    # Create an already-expired token (-5 minutes)
    expired_token = create_access_token(subject=1, expires_delta=timedelta(minutes=-5))
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 401

