from typing import Optional

from flask import Flask, g, request
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from app.api.routes.auth import auth_bp
from app.api.routes.health import health_bp
from app.api.routes.products import products_bp
from app.constants import APIMessages, APIProblemCodes, HTTPStatusCodes
from app.core.config import get_config
from app.core.extensions import init_extensions, jwt
from app.db.base import import_models
from app.utils.logger import configure_logging
from app.utils.problem import make_problem_response


def create_app(config_name: Optional[str] = None) -> Flask:
    """Create and configure the Flask application instance.

    Args:
        config_name: Optional configuration profile name.

    Returns:
        The configured Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    configure_logging(app)
    init_extensions(app)
    import_models()

    register_request_hooks(app)
    register_error_handlers(app)
    register_jwt_error_handlers()
    register_blueprints(app)

    return app


def register_request_hooks(app: Flask) -> None:
    """Register global request lifecycle hooks.

    Args:
        app: The Flask application.
    """
    @app.before_request
    def attach_trace_id() -> None:
        """Attach a request trace identifier to Flask global context."""
        g.trace_id = request.headers.get("X-Trace-Id")


def register_blueprints(app: Flask) -> None:
    """Register all API blueprints on the Flask app.

    Args:
        app: The Flask application.
    """
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)


def register_error_handlers(app: Flask) -> None:
    """Register application-wide exception handlers.

    Args:
        app: The Flask application.
    """
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        """Convert Marshmallow validation errors to problem responses."""
        return make_problem_response(
            status=HTTPStatusCodes.UNPROCESSABLE_ENTITY,
            title=APIMessages.VALIDATION_ERROR,
            detail=APIMessages.REQUEST_VALIDATION_FAILED,
            code=APIProblemCodes.VALIDATION_ERROR,
            errors=err.messages,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        """Convert Werkzeug HTTP exceptions to problem responses."""
        return make_problem_response(
            status=err.code or HTTPStatusCodes.INTERNAL_SERVER_ERROR,
            title=err.name,
            detail=err.description,
            code=APIProblemCodes.HTTP_ERROR,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(_err: Exception):
        """Convert uncaught exceptions to internal error responses."""
        return make_problem_response(
            status=HTTPStatusCodes.INTERNAL_SERVER_ERROR,
            title=APIMessages.INTERNAL_SERVER_ERROR,
            detail=APIMessages.INTERNAL_UNEXPECTED_ERROR,
            code=APIProblemCodes.INTERNAL_ERROR,
        )


def register_jwt_error_handlers() -> None:
    """Register JWT-specific error handlers."""
    @jwt.unauthorized_loader
    def unauthorized_response(_reason: str):
        """Handle requests with missing authentication credentials."""
        return make_problem_response(
            status=HTTPStatusCodes.UNAUTHORIZED,
            title=APIMessages.UNAUTHORIZED,
            detail=APIMessages.MISSING_OR_INVALID_AUTH_TOKEN,
            code=APIProblemCodes.UNAUTHORIZED,
        )

    @jwt.invalid_token_loader
    def invalid_token_response(_reason: str):
        """Handle requests with invalid JWT tokens."""
        return make_problem_response(
            status=HTTPStatusCodes.UNAUTHORIZED,
            title=APIMessages.UNAUTHORIZED,
            detail=APIMessages.INVALID_AUTH_TOKEN,
            code=APIProblemCodes.INVALID_TOKEN,
        )

    @jwt.expired_token_loader
    def expired_token_response(_jwt_header, _jwt_payload):
        """Handle requests with expired JWT tokens."""
        return make_problem_response(
            status=HTTPStatusCodes.UNAUTHORIZED,
            title=APIMessages.UNAUTHORIZED,
            detail=APIMessages.EXPIRED_AUTH_TOKEN,
            code=APIProblemCodes.TOKEN_EXPIRED,
        )
