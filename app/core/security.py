from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a plain-text password using configured password context.

    Args:
        password: Plain-text password.

    Returns:
        A secure password hash string.
    """
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored hash.

    Args:
        password: Plain-text password to verify.
        password_hash: Previously stored password hash.

    Returns:
        True if password matches the hash, else False.
    """
    return pwd_context.verify(password, password_hash)
