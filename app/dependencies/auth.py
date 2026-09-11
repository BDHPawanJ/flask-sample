from flask_jwt_extended import get_jwt_identity, jwt_required
from typing import Optional

from app.models.user import User


def require_auth(func):
    """Wrap a route handler with JWT authentication enforcement.

    Args:
        func: Route handler function.

    Returns:
        The JWT-protected route handler.
    """
    return jwt_required()(func)


def get_current_user() -> Optional[User]:
    """Resolve the authenticated user from JWT identity.

    Returns:
        The matching user when identity is present and valid, otherwise None.
    """
    identity = get_jwt_identity()
    if identity is None:
        return None
    return User.query.filter_by(public_id=identity).first()
