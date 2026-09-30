from flask import Blueprint, request

from app.constants import APIMessages, APIProblemCodes, HTTPStatusCodes
from app.dependencies.auth import get_current_user, require_auth
from app.schemas.auth import LoginRequestSchema, RegisterRequestSchema
from app.services.auth_service import AuthService, EmailAlreadyExistsError
from app.services.idempotency_service import IdempotencyService
from app.utils.problem import make_problem_response
from app.utils.responses import json_response

auth_bp = Blueprint("auth", __name__, url_prefix="/v1/auth")

register_schema = RegisterRequestSchema()
login_schema = LoginRequestSchema()


@auth_bp.post("/register")
def register():
    """Register a new user with idempotent request handling.

    Returns:
        A problem response on validation/conflict errors, or the created user payload.
    """
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return make_problem_response(
            status=HTTPStatusCodes.BAD_REQUEST,
            title=APIMessages.BAD_REQUEST,
            detail=APIMessages.MISSING_IDEMPOTENCY_KEY,
            code=APIProblemCodes.MISSING_IDEMPOTENCY_KEY,
        )

    payload = register_schema.load(request.get_json(silent=True) or {})
    request_hash = IdempotencyService.build_request_hash(payload)
    record = IdempotencyService.get_record(
        idempotency_key=idempotency_key,
        operation="auth_register",
        principal_key="",
    )
    if record:
        if record.request_hash != request_hash:
            return make_problem_response(
                status=HTTPStatusCodes.CONFLICT,
                title=APIMessages.CONFLICT,
                detail=APIMessages.IDEMPOTENCY_PAYLOAD_MISMATCH,
                code=APIProblemCodes.IDEMPOTENCY_PAYLOAD_MISMATCH,
            )
        replay = IdempotencyService.replay_result(record)
        return json_response(replay.body, replay.status)

    try:
        user = AuthService.register_user(
            email=payload["email"],
            password=payload["password"],
        )
    except EmailAlreadyExistsError as err:
        return make_problem_response(
            status=HTTPStatusCodes.CONFLICT,
            title=APIMessages.CONFLICT,
            detail=str(err) if str(err) else APIMessages.EMAIL_ALREADY_EXISTS,
            code=APIProblemCodes.CONFLICT,
        )

    body = AuthService.serialize_user(user)
    IdempotencyService.save_record(
        idempotency_key=idempotency_key,
        operation="auth_register",
        principal_key="",
        request_hash=request_hash,
        response_status=HTTPStatusCodes.CREATED,
        response_body=body,
    )
    return json_response(body, HTTPStatusCodes.CREATED)


@auth_bp.post("/login")
def login():
    """Authenticate a user and issue an access token.

    Returns:
        A problem response on authentication failure, or login payload with token.
    """
    payload = login_schema.load(request.get_json(silent=True) or {})
    user = AuthService.authenticate_user(payload["email"], payload["password"])
    if user is None:
        return make_problem_response(
            status=HTTPStatusCodes.UNAUTHORIZED,
            title=APIMessages.UNAUTHORIZED,
            detail=APIMessages.INVALID_EMAIL_OR_PASSWORD,
            code=APIProblemCodes.INVALID_CREDENTIALS,
        )
    body = {
        "access_token": AuthService.issue_access_token(user),
        "token_type": "bearer",
        "user": AuthService.serialize_user(user),
    }
    return json_response(body, HTTPStatusCodes.OK)


@auth_bp.get("/me")
@require_auth
def me():
    """Return the authenticated user's profile.

    Returns:
        A problem response when user resolution fails, or user profile payload.
    """
    user = get_current_user()
    if user is None:
        return make_problem_response(
            status=HTTPStatusCodes.UNAUTHORIZED,
            title=APIMessages.UNAUTHORIZED,
            detail=APIMessages.AUTHENTICATED_USER_RESOLUTION_FAILED,
            code=APIProblemCodes.UNAUTHORIZED,
        )
    return json_response(AuthService.serialize_user(user), HTTPStatusCodes.OK)
