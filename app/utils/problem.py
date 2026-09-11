import uuid
from typing import Any
from typing import Optional

from flask import Response, g, jsonify, request


def make_problem_response(
    *,
    status: int,
    title: str,
    detail: str,
    code: str,
    type_uri: str = "about:blank",
    errors: Optional[dict[str, Any]] = None,
) -> tuple[Response, int]:
    """Build an RFC7807-compatible problem+json response.

    Args:
        status: HTTP status code.
        title: Short error title.
        detail: Human-readable error detail.
        code: Application-specific machine-readable code.
        type_uri: Problem type URI.
        errors: Optional structured validation errors.

    Returns:
        Tuple of Flask response and status code.
    """
    trace_id = getattr(g, "trace_id", None) or str(uuid.uuid4())
    payload: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path,
        "code": code,
        "trace_id": trace_id,
    }
    if errors is not None:
        payload["errors"] = errors

    response = jsonify(payload)
    response.headers["Content-Type"] = "application/problem+json"
    return response, status
