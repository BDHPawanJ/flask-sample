"""HTTP status code constants used by the API."""


class HTTPStatusCodes:
    """Centralized HTTP status codes used throughout the API."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    CONFLICT = 409
    PRECONDITION_FAILED = 412
    PRECONDITION_REQUIRED = 428
    UNPROCESSABLE_ENTITY = 422

    INTERNAL_SERVER_ERROR = 500
