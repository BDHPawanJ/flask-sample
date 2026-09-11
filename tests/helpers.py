def login_user(client, email: str, password: str = "strongpass123"):
    """Send a login request for a test user.

    Args:
        client: Flask test client.
        email: User email.
        password: User password.

    Returns:
        Flask test response object.
    """
    return client.post("/v1/auth/login", json={"email": email, "password": password})


def auth_headers(token: str) -> dict[str, str]:
    """Build authorization headers for authenticated test requests.

    Args:
        token: JWT access token.

    Returns:
        Header dictionary containing bearer token.
    """
    return {"Authorization": f"Bearer {token}"}
