"""Reusable response builders for API endpoints."""

from typing import Any, Optional

from flask import Response, jsonify


def json_response(
    body: dict[str, Any],
    status_code: int,
    headers: Optional[dict[str, str]] = None,
) -> tuple[Response, int]:
    """Build a JSON response with optional headers.

    Args:
        body: JSON-serializable response body.
        status_code: HTTP status code.
        headers: Optional response headers.

    Returns:
        Tuple of Flask response and status code.
    """
    response = jsonify(body)
    if headers:
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
    return response, status_code


def no_content_response(status_code: int) -> tuple[str, int]:
    """Build an empty-body response.

    Args:
        status_code: HTTP status code.

    Returns:
        Empty body and HTTP status code tuple.
    """
    return "", status_code
