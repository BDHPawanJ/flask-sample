from flask_jwt_extended import create_access_token
from typing import Optional, Union

from app.core.extensions import db
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.utils.serialization import to_iso_z


class EmailAlreadyExistsError(ValueError):
    """Raised when registration is attempted with an existing email."""


class AuthService:
    """Business logic for authentication and user identity operations."""

    @staticmethod
    def register_user(email: str, password: str) -> User:
        """Create and persist a new user account.

        Args:
            email: User email address.
            password: Plain-text password.

        Returns:
            The newly created User instance.

        Raises:
            ValueError: If an account with the same email already exists.
        """
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is not None:
            raise EmailAlreadyExistsError("Email already exists.")

        user = User(email=email, password_hash=hash_password(password), is_active=True)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password.

        Args:
            email: User email address.
            password: Plain-text password.

        Returns:
            The authenticated User, or None when credentials are invalid.
        """
        user = User.query.filter_by(email=email).first()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def issue_access_token(user: User) -> str:
        """Issue a JWT access token for a user.

        Args:
            user: Authenticated user.

        Returns:
            Signed JWT access token string.
        """
        return create_access_token(identity=user.public_id)

    @staticmethod
    def serialize_user(user: User) -> dict[str, Union[str, bool]]:
        """Serialize a User model to API response shape.

        Args:
            user: User model instance.

        Returns:
            Serialized user payload.
        """
        return {
            "user_id": user.public_id,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": to_iso_z(user.created_at),
            "updated_at": to_iso_z(user.updated_at),
        }
