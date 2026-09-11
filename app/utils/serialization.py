from datetime import datetime, timezone
from decimal import Decimal


def to_iso_z(value: datetime) -> str:
    """Convert a datetime to UTC ISO-8601 string with Z suffix.

    Args:
        value: Datetime value to convert.

    Returns:
        UTC datetime string without microseconds and with trailing ``Z``.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def decimal_to_string(value: Decimal) -> str:
    """Convert a Decimal to a plain string representation.

    Args:
        value: Decimal value.

    Returns:
        Non-scientific decimal string.
    """
    return format(value, "f")
