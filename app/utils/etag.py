import hashlib

from app.models.product import Product


def compute_product_etag(product: Product) -> str:
    """Compute an ETag for a product resource version.

    Args:
        product: Product model instance.

    Returns:
        Strong ETag string wrapped in double quotes.
    """
    digest = hashlib.sha256(
        f"{product.id}:{product.updated_at.isoformat()}".encode("utf-8")
    ).hexdigest()
    return f"\"{digest}\""
