import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from typing import Optional

from app.core.extensions import db
from app.models.idempotency_key import IdempotencyKey


@dataclass
class IdempotencyReplayResult:
    """DTO for replaying previously stored idempotent responses."""

    status: int
    body: dict[str, Any]


class IdempotencyService:
    """Utilities for request idempotency persistence and replay."""

    @staticmethod
    def _json_default(value: Any) -> str:
        """Serialize non-standard values for deterministic JSON hashing.

        Args:
            value: Value to serialize.

        Returns:
            String representation for supported types.

        Raises:
            TypeError: If the value type is unsupported.
        """
        if isinstance(value, Decimal):
            return format(value, "f")
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    @staticmethod
    def build_request_hash(payload: dict[str, Any]) -> str:
        """Build a deterministic request payload hash.

        Args:
            payload: Request body payload.

        Returns:
            SHA-256 hash of normalized JSON payload.
        """
        normalized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=IdempotencyService._json_default,
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def get_record(
        *,
        idempotency_key: str,
        operation: str,
        principal_key: str,
    ) -> Optional[IdempotencyKey]:
        """Fetch an idempotency record by key, operation, and principal.

        Args:
            idempotency_key: Idempotency key value.
            operation: Logical operation identifier.
            principal_key: Principal-scoped key (for example, user id).

        Returns:
            Matching IdempotencyKey record, or None when absent.
        """
        return IdempotencyKey.query.filter_by(
            idempotency_key=idempotency_key,
            operation=operation,
            principal_key=principal_key,
        ).first()

    @staticmethod
    def replay_result(record: IdempotencyKey) -> IdempotencyReplayResult:
        """Reconstruct a replayable response from a stored record.

        Args:
            record: Stored idempotency record.

        Returns:
            Rehydrated response status and body payload.
        """
        return IdempotencyReplayResult(
            status=record.response_status,
            body=json.loads(record.response_body),
        )

    @staticmethod
    def save_record(
        *,
        idempotency_key: str,
        operation: str,
        principal_key: str,
        request_hash: str,
        response_status: int,
        response_body: dict[str, Any],
    ) -> None:
        """Persist an idempotency snapshot for future replay.

        Args:
            idempotency_key: Idempotency key value.
            operation: Logical operation identifier.
            principal_key: Principal-scoped key (for example, user id).
            request_hash: Deterministic hash of request payload.
            response_status: HTTP status code to replay.
            response_body: Response payload to replay.
        """
        record = IdempotencyKey(
            idempotency_key=idempotency_key,
            operation=operation,
            principal_key=principal_key,
            request_hash=request_hash,
            response_status=response_status,
            response_body=json.dumps(response_body, separators=(",", ":"), sort_keys=True),
        )
        db.session.add(record)
        db.session.commit()
