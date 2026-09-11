from datetime import timedelta
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_ROOT / ".env"
ENV_VALUES = dotenv_values(ENV_FILE_PATH)


def _require_env(key: str) -> str:
    """Read a required environment variable from the loaded .env values.

    Args:
        key: Environment variable name.

    Returns:
        The non-empty environment value.

    Raises:
        RuntimeError: If the value is missing or empty.
    """
    value = ENV_VALUES.get(key)
    if value is None or str(value).strip() == "":
        raise RuntimeError(
            f"Missing required environment variable '{key}' in {ENV_FILE_PATH}."
        )
    return value


class BaseConfig:
    """Base Flask configuration shared by all environments."""
    SECRET_KEY = _require_env("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _require_env("DATABASE_URL")
    JWT_SECRET_KEY = _require_env("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(_require_env("JWT_ACCESS_TOKEN_EXPIRES_MINUTES")))
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True


class DevelopmentConfig(BaseConfig):
    """Configuration for local development."""
    DEBUG = True


class TestingConfig(BaseConfig):
    """Configuration used during test execution."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _require_env("TEST_DATABASE_URL")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)


class ProductionConfig(BaseConfig):
    """Configuration for production deployments."""
    DEBUG = False


def get_config(config_name: Optional[str]):
    """Resolve the active config class by explicit name or FLASK_ENV.

    Args:
        config_name: Optional explicit config name.

    Returns:
        A Flask configuration class.
    """
    if config_name:
        normalized = config_name.lower()
    else:
        normalized = ENV_VALUES.get("FLASK_ENV", "development").lower()

    if normalized == "production":
        return ProductionConfig
    if normalized == "testing":
        return TestingConfig
    return DevelopmentConfig
