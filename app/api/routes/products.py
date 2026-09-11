from marshmallow import ValidationError
from flask import Blueprint, request

from app.constants import APIMessages, APIProblemCodes, HTTPStatusCodes
from app.dependencies.auth import get_current_user, require_auth
from app.schemas.product import ProductCreateSchema, ProductPatchSchema
from app.services.idempotency_service import IdempotencyService
from app.services.product_service import ProductService
from app.utils.etag import compute_product_etag
from app.utils.problem import make_problem_response
from app.utils.responses import json_response, no_content_response

products_bp = Blueprint("products", __name__, url_prefix="/v1/products")

create_schema = ProductCreateSchema()
patch_schema = ProductPatchSchema()


@products_bp.post("")
@require_auth
def create_product():
    """Create a product with idempotency protection.

    Returns:
        A problem response on validation/auth/idempotency errors, or created product payload.
    """
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return make_problem_response(
            status=HTTPStatusCodes.BAD_REQUEST,
            title=APIMessages.BAD_REQUEST,
            detail=APIMessages.MISSING_IDEMPOTENCY_KEY,
            code=APIProblemCodes.MISSING_IDEMPOTENCY_KEY,
        )

    user = get_current_user()
    if user is None:
        return make_problem_response(
            status=HTTPStatusCodes.UNAUTHORIZED,
            title=APIMessages.UNAUTHORIZED,
            detail=APIMessages.AUTHENTICATED_USER_RESOLUTION_FAILED,
            code=APIProblemCodes.UNAUTHORIZED,
        )

    payload = create_schema.load(request.get_json(silent=True) or {})
    request_hash = IdempotencyService.build_request_hash(payload)
    principal_key = user.public_id

    record = IdempotencyService.get_record(
        idempotency_key=idempotency_key,
        operation="products_create",
        principal_key=principal_key,
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

    product = ProductService.create_product(
        name=payload["name"],
        description=payload.get("description"),
        price=payload["price"],
        stock=payload["stock"],
    )
    body = ProductService.serialize_product(product)
    IdempotencyService.save_record(
        idempotency_key=idempotency_key,
        operation="products_create",
        principal_key=principal_key,
        request_hash=request_hash,
        response_status=HTTPStatusCodes.CREATED,
        response_body=body,
    )
    return json_response(
        body,
        HTTPStatusCodes.CREATED,
        headers={"ETag": compute_product_etag(product)},
    )


@products_bp.get("")
def list_products():
    """List products with optional cursor pagination and search filtering.

    Returns:
        A problem response for invalid query params, or paginated products payload.
    """
    limit = request.args.get("limit", default=10, type=int)
    cursor = request.args.get("cursor", default=None, type=str)
    search = request.args.get("search", default=None, type=str)
    if limit < 1 or limit > 100:
        return make_problem_response(
            status=HTTPStatusCodes.UNPROCESSABLE_ENTITY,
            title=APIMessages.VALIDATION_ERROR,
            detail=APIMessages.LIMIT_OUT_OF_RANGE,
            code=APIProblemCodes.VALIDATION_ERROR,
            errors={"limit": ["Must be between 1 and 100."]},
        )

    try:
        result = ProductService.list_products(limit=limit, cursor=cursor, search=search)
    except (ValueError, ValidationError):
        return make_problem_response(
            status=HTTPStatusCodes.UNPROCESSABLE_ENTITY,
            title=APIMessages.VALIDATION_ERROR,
            detail=APIMessages.INVALID_CURSOR,
            code=APIProblemCodes.INVALID_CURSOR,
        )
    return json_response(result, HTTPStatusCodes.OK)


@products_bp.get("/<string:product_id>")
def get_product(product_id: str):
    """Return a single product by public identifier.

    Args:
        product_id: Public product identifier.

    Returns:
        A problem response when product is missing, or the product payload.
    """
    product = ProductService.get_product_by_public_id(product_id)
    if product is None:
        return make_problem_response(
            status=HTTPStatusCodes.NOT_FOUND,
            title=APIMessages.NOT_FOUND,
            detail=APIMessages.PRODUCT_NOT_FOUND,
            code=APIProblemCodes.NOT_FOUND,
        )
    body = ProductService.serialize_product(product)
    return json_response(
        body,
        HTTPStatusCodes.OK,
        headers={"ETag": compute_product_etag(product)},
    )


@products_bp.patch("/<string:product_id>")
@require_auth
def patch_product(product_id: str):
    """Partially update a product using optimistic concurrency via ETag.

    Args:
        product_id: Public product identifier.

    Returns:
        A problem response on auth/precondition/validation failures, or updated payload.
    """
    if_match = request.headers.get("If-Match")
    if if_match is None:
        return make_problem_response(
            status=HTTPStatusCodes.PRECONDITION_REQUIRED,
            title=APIMessages.PRECONDITION_REQUIRED,
            detail=APIMessages.MISSING_IF_MATCH,
            code=APIProblemCodes.MISSING_IF_MATCH,
        )

    product = ProductService.get_product_by_public_id(product_id)
    if product is None:
        return make_problem_response(
            status=HTTPStatusCodes.NOT_FOUND,
            title=APIMessages.NOT_FOUND,
            detail=APIMessages.PRODUCT_NOT_FOUND,
            code=APIProblemCodes.NOT_FOUND,
        )

    current_etag = compute_product_etag(product)
    if if_match != current_etag:
        return make_problem_response(
            status=HTTPStatusCodes.PRECONDITION_FAILED,
            title=APIMessages.PRECONDITION_FAILED,
            detail=APIMessages.ETAG_MISMATCH,
            code=APIProblemCodes.ETAG_MISMATCH,
        )

    payload = patch_schema.load(request.get_json(silent=True) or {}, partial=True)
    if not payload:
        return make_problem_response(
            status=HTTPStatusCodes.UNPROCESSABLE_ENTITY,
            title=APIMessages.VALIDATION_ERROR,
            detail=APIMessages.PATCH_BODY_REQUIRED,
            code=APIProblemCodes.VALIDATION_ERROR,
        )
    updated = ProductService.patch_product(product, payload)
    body = ProductService.serialize_product(updated)
    return json_response(
        body,
        HTTPStatusCodes.OK,
        headers={"ETag": compute_product_etag(updated)},
    )


@products_bp.delete("/<string:product_id>")
@require_auth
def delete_product(product_id: str):
    """Delete a product by public identifier.

    Args:
        product_id: Public product identifier.

    Returns:
        No-content response when deleted, otherwise a not-found problem response.
    """
    product = ProductService.get_product_by_public_id(product_id)
    if product is None:
        return make_problem_response(
            status=HTTPStatusCodes.NOT_FOUND,
            title=APIMessages.NOT_FOUND,
            detail=APIMessages.PRODUCT_NOT_FOUND,
            code=APIProblemCodes.NOT_FOUND,
        )
    ProductService.delete_product(product)
    return no_content_response(HTTPStatusCodes.NO_CONTENT)
