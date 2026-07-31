"""Shared test setup using an isolated in-memory database."""

import os

import pytest


os.environ["DATABASE_URI"] = "sqlite:///:memory:"

from app import app as flask_app  # noqa: E402
from data_models import db  # noqa: E402


@pytest.fixture()
def app():
    """Provide the Flask app with fresh tables for each test."""
    flask_app.config.update(TESTING=True, SECRET_KEY="test-secret")

    with flask_app.app_context():
        db.drop_all()
        db.create_all()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Provide a browser-like Flask test client."""
    return app.test_client()
