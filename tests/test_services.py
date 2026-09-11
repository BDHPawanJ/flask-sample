from decimal import Decimal

from app.services.idempotency_service import IdempotencyService
from app.services.product_service import ProductService
from app.utils.cursor import decode_cursor, encode_cursor


def test_idempotency_hash_consistent():
    """Ensure idempotency hash is deterministic for key-order variations."""
    payload_a = {"a": 1, "b": "x"}
    payload_b = {"b": "x", "a": 1}
    assert IdempotencyService.build_request_hash(payload_a) == IdempotencyService.build_request_hash(
        payload_b
    )


def test_cursor_round_trip():
    """Ensure cursor encode/decode round-trip preserves id value."""
    encoded = encode_cursor(123)
    decoded = decode_cursor(encoded)
    assert decoded == 123


def test_product_service_serialize_formats_price_and_ids(app, db_clean):
    """Ensure product serialization formats price and timestamp fields."""
    with app.app_context():
        product = ProductService.create_product(
            name="Demo",
            description="desc",
            price=Decimal("12.50"),
            stock=4,
        )
        serialized = ProductService.serialize_product(product)

    assert serialized["product_id"]
    assert serialized["price"] == "12.50"
    assert serialized["created_at"].endswith("Z")
    assert serialized["updated_at"].endswith("Z")
