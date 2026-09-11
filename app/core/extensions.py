from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def init_extensions(app: Flask) -> None:
    """Initialize Flask extensions for the application.

    Args:
        app: The Flask application.
    """
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
