def import_models() -> None:
    """Import all SQLAlchemy models so metadata includes all tables."""
    # Imported for side effects so SQLAlchemy metadata sees all tables.
    from app.models import idempotency_key, product, user  # noqa: F401
