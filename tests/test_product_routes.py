import uuid
from decimal import Decimal

import pytest

from app.core.extensions import db
from app.models.product import Product
from tests.helpers import auth_headers, login_user

pytestmark = pytest.mark.usefixtures("db_clean")


def _register_and_login(client, email: str) -> str:
    """Register and authenticate a user, returning an access token."""
    register = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "strongpass123"},
        headers={"Idempotency-Key": f"reg-{uuid.uuid4()}"},
    )
    assert register.status_code == 201
    login = login_user(client, email)
    assert login.status_code == 200
    return login.json["access_token"]


def test_create_product_requires_auth(client):
    """Ensure product creation is protected by authentication."""
    response = client.post(
        "/v1/products",
        json={"name": "Widget", "description": "desc", "price": "9.99", "stock": 2},
        headers={"Idempotency-Key": f"prd-{uuid.uuid4()}"},
    )
    assert response.status_code == 401


def test_create_product_idempotency_replay_and_mismatch(client, unique_email):
    """Ensure product create idempotency replays and detects mismatched payloads."""
    token = _register_and_login(client, unique_email)
    key = f"prd-{uuid.uuid4()}"

    payload = {"name": "Widget", "description": "desc", "price": "9.99", "stock": 2}
    first = client.post(
        "/v1/products",
        json=payload,
        headers={**auth_headers(token), "Idempotency-Key": key},
    )
    second = client.post(
        "/v1/products",
        json=payload,
        headers={**auth_headers(token), "Idempotency-Key": key},
    )
    mismatch = client.post(
        "/v1/products",
        json={"name": "Other", "description": "desc", "price": "10.99", "stock": 2},
        headers={**auth_headers(token), "Idempotency-Key": key},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json == second.json
    assert mismatch.status_code == 409
    assert mismatch.json["code"] == "idempotency_payload_mismatch"


def test_cursor_pagination_flow(client, app):
    """Ensure cursor pagination returns expected page boundaries."""
    with app.app_context():
        for i in range(1, 5):
            db.session.add(
                Product(
                    name=f"Prod-{i}",
                    description=None,
                    price=Decimal("10.00"),
                    stock=i,
                )
            )
        db.session.commit()

    first = client.get("/v1/products?limit=2")
    assert first.status_code == 200
    assert len(first.json["items"]) == 2
    assert first.json["has_more"] is True
    assert first.json["next_cursor"] is not None

    second = client.get(f"/v1/products?limit=2&cursor={first.json['next_cursor']}")
    assert second.status_code == 200
    assert len(second.json["items"]) == 2
    assert second.json["has_more"] is False
    assert second.json["next_cursor"] is None


def test_etag_mismatch_on_patch(client, unique_email):
    """Ensure patch requests fail when If-Match uses stale ETag."""
    token = _register_and_login(client, unique_email)
    create = client.post(
        "/v1/products",
        json={"name": "Widget", "description": "desc", "price": "9.99", "stock": 2},
        headers={**auth_headers(token), "Idempotency-Key": f"prd-{uuid.uuid4()}"},
    )
    assert create.status_code == 201
    product_id = create.json["product_id"]

    patch = client.patch(
        f"/v1/products/{product_id}",
        json={"stock": 10},
        headers={**auth_headers(token), "If-Match": "\"stale-etag\""},
    )
    assert patch.status_code == 412
    assert patch.json["code"] == "etag_mismatch"


def test_patch_success_returns_new_etag(client, unique_email):
    """Ensure successful patch returns updated ETag and modified data."""
    token = _register_and_login(client, unique_email)
    create = client.post(
        "/v1/products",
        json={"name": "Widget", "description": "desc", "price": "9.99", "stock": 2},
        headers={**auth_headers(token), "Idempotency-Key": f"prd-{uuid.uuid4()}"},
    )
    product_id = create.json["product_id"]
    old_etag = create.headers["ETag"]

    patch = client.patch(
        f"/v1/products/{product_id}",
        json={"stock": 3},
        headers={**auth_headers(token), "If-Match": old_etag},
    )

    assert patch.status_code == 200
    assert patch.json["stock"] == 3
    assert patch.headers["ETag"] != old_etag


def test_delete_product(client, unique_email):
    """Ensure product deletion succeeds and resource is no longer retrievable."""
    token = _register_and_login(client, unique_email)
    create = client.post(
        "/v1/products",
        json={"name": "Widget", "description": "desc", "price": "9.99", "stock": 2},
        headers={**auth_headers(token), "Idempotency-Key": f"prd-{uuid.uuid4()}"},
    )
    product_id = create.json["product_id"]

    delete = client.delete(f"/v1/products/{product_id}", headers=auth_headers(token))
    assert delete.status_code == 204

    get_deleted = client.get(f"/v1/products/{product_id}")
    assert get_deleted.status_code == 404
