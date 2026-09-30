import uuid

import pytest

from tests.helpers import login_user

pytestmark = pytest.mark.usefixtures("db_clean")


def test_register_requires_idempotency_key(client, unique_email):
    """Ensure registration fails when Idempotency-Key header is missing."""
    response = client.post(
        "/v1/auth/register",
        json={"email": unique_email, "password": "strongpass123"},
    )
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json["code"] == "missing_idempotency_key"


def test_register_idempotency_replay(client, unique_email):
    """Ensure identical registration requests replay successfully."""
    key = f"same-key-{uuid.uuid4()}"
    payload = {"email": unique_email, "password": "strongpass123"}

    first = client.post("/v1/auth/register", json=payload, headers={"Idempotency-Key": key})
    second = client.post("/v1/auth/register", json=payload, headers={"Idempotency-Key": key})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json == second.json


def test_register_idempotency_payload_mismatch_conflict(client):
    """Ensure reusing idempotency key with different payload returns conflict."""
    key = f"same-key-{uuid.uuid4()}"
    first = client.post(
        "/v1/auth/register",
        json={"email": "first@example.com", "password": "strongpass123"},
        headers={"Idempotency-Key": key},
    )
    second = client.post(
        "/v1/auth/register",
        json={"email": "second@example.com", "password": "strongpass123"},
        headers={"Idempotency-Key": key},
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json["code"] == "idempotency_payload_mismatch"


def test_login_and_me(client, unique_email):
    """Ensure login succeeds and /me returns the authenticated user."""
    register = client.post(
        "/v1/auth/register",
        json={"email": unique_email, "password": "strongpass123"},
        headers={"Idempotency-Key": f"reg-{uuid.uuid4()}"},
    )
    assert register.status_code == 201

    login = login_user(client, unique_email)
    assert login.status_code == 200
    token = login.json["access_token"]

    me_response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json["email"] == unique_email


def test_register_accepts_password_longer_than_bcrypt_limit(client, unique_email):
    """Ensure registration works for passwords longer than bcrypt's 72-byte limit."""
    long_password = "a" * 100
    response = client.post(
        "/v1/auth/register",
        json={"email": unique_email, "password": long_password},
        headers={"Idempotency-Key": f"reg-{uuid.uuid4()}"},
    )
    assert response.status_code == 201
    assert response.json["email"] == unique_email


def test_me_unauthorized(client):
    """Ensure /me requires authentication."""
    response = client.get("/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["Content-Type"] == "application/problem+json"
