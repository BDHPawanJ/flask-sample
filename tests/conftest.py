import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app import create_app
from app.core.extensions import db


@pytest.fixture(scope="session")
def app():
    """Create a configured Flask app fixture for tests."""
    os.environ.setdefault(
        "TEST_DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/flask_sample_test",
    )
    app = create_app("testing")
    yield app


@pytest.fixture()
def client(app):
    """Return a Flask test client fixture."""
    return app.test_client()


@pytest.fixture(scope="session")
def db_ready(app):
    """Ensure test database connectivity and initialize schema."""
    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
            db.session.commit()
        except OperationalError as err:
            pytest.skip(f"MySQL test database is not reachable: {err}")
        db.drop_all()
        db.create_all()
    yield
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def db_clean(app, db_ready):
    """Clean all tables before each test."""
    with app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
    yield


@pytest.fixture()
def unique_email():
    """Generate a unique email address for isolated tests."""
    return f"user-{uuid.uuid4().hex[:12]}@example.com"
