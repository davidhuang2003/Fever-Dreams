import pytest

from app import create_app


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_URL": None,
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()

