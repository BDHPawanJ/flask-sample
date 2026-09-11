from decimal import Decimal
from typing import Optional

from app.core.extensions import db
from app.models.product import Product
from app.utils.cursor import decode_cursor, encode_cursor
from app.utils.serialization import decimal_to_string, to_iso_z


class ProductService:
    """Business logic for product CRUD and response serialization."""

    @staticmethod
    def create_product(
        *,
        name: str,
        description: Optional[str],
        price: Decimal,
        stock: int,
    ) -> Product:
        """Create and persist a product.

        Args:
            name: Product name.
            description: Optional product description.
            price: Product unit price.
            stock: Available stock quantity.

        Returns:
            The newly created Product instance.
        """
        product = Product(name=name, description=description, price=price, stock=stock)
        db.session.add(product)
        db.session.commit()
        db.session.refresh(product)
        return product

    @staticmethod
    def get_product_by_public_id(product_id: str) -> Optional[Product]:
        """Look up a product by public identifier.

        Args:
            product_id: Public product identifier.

        Returns:
            Matching Product when found, otherwise None.
        """
        return Product.query.filter_by(public_id=product_id).first()

    @staticmethod
    def list_products(
        *,
        limit: int,
        cursor: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict[str, object]:
        """List products with cursor pagination and optional name search.

        Args:
            limit: Maximum number of items to return.
            cursor: Optional encoded cursor from a previous page.
            search: Optional case-insensitive product name query.

        Returns:
            Paginated response containing items, next cursor, and has_more flag.
        """
        query = Product.query.order_by(Product.id.asc())
        if search:
            like_expression = f"%{search}%"
            query = query.filter(Product.name.ilike(like_expression))
        if cursor:
            last_seen_id = decode_cursor(cursor)
            query = query.filter(Product.id > last_seen_id)

        rows = query.limit(limit + 1).all()
        has_more = len(rows) > limit
        selected = rows[:limit]
        next_cursor = encode_cursor(selected[-1].id) if has_more and selected else None

        return {
            "items": [ProductService.serialize_product(item) for item in selected],
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

    @staticmethod
    def patch_product(product: Product, changes: dict[str, object]) -> Product:
        """Apply partial updates to a product and persist changes.

        Args:
            product: Product model to update.
            changes: Partial field updates.

        Returns:
            Updated Product instance.
        """
        for field_name in ("name", "description", "price", "stock"):
            if field_name in changes:
                setattr(product, field_name, changes[field_name])
        product.touch_updated_at()
        db.session.add(product)
        db.session.commit()
        db.session.refresh(product)
        return product

    @staticmethod
    def delete_product(product: Product) -> None:
        """Delete a product record.

        Args:
            product: Product model to delete.
        """
        db.session.delete(product)
        db.session.commit()

    @staticmethod
    def serialize_product(product: Product) -> dict[str, object]:
        """Serialize a Product model to API response shape.

        Args:
            product: Product model instance.

        Returns:
            Serialized product payload.
        """
        return {
            "product_id": product.public_id,
            "name": product.name,
            "description": product.description,
            "price": decimal_to_string(product.price),
            "stock": product.stock,
            "created_at": to_iso_z(product.created_at),
            "updated_at": to_iso_z(product.updated_at),
        }
