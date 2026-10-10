import pytest

from db import get_db


def test_missing_database_url_has_clear_error(app):
    with app.app_context(), pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_db()


@pytest.mark.skip(reason="Requires a disposable PostgreSQL test database and initialized schema.")
def test_schema_enforces_one_choice_per_decision():
    """Add an integration test once the test database fixture exists."""

