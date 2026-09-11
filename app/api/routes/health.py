from flask import Blueprint

from app.constants import HTTPStatusCodes
from app.utils.responses import json_response

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """Return a lightweight health status response."""
    return json_response({"status": "ok"}, HTTPStatusCodes.OK)
