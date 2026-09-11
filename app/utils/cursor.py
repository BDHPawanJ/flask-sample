import base64
import binascii


def encode_cursor(last_seen_id: int) -> str:
    """Encode the last-seen integer id as a URL-safe cursor.

    Args:
        last_seen_id: Last item database id.

    Returns:
        URL-safe base64 encoded cursor.
    """
    raw_value = str(last_seen_id).encode("utf-8")
    return base64.urlsafe_b64encode(raw_value).decode("utf-8")


def decode_cursor(cursor: str) -> int:
    """Decode a URL-safe cursor into an integer id.

    Args:
        cursor: URL-safe base64 encoded cursor.

    Returns:
        Decoded integer id.

    Raises:
        ValueError: If cursor is malformed or non-numeric.
    """
    try:
        raw_value = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        return int(raw_value)
    except (ValueError, binascii.Error) as err:
        raise ValueError("Invalid cursor value.") from err
