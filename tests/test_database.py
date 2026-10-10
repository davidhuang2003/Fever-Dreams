import pytest

import db


def test_missing_database_url_has_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db.connect()


def test_seed_loads_the_storm_scenario(connection):
    scenario = connection.execute("SELECT * FROM scenarios").fetchone()
    assert scenario["title"] == "The Long Night"
    assert scenario["is_published"] is True


def test_setup_can_run_twice_without_duplicates(connection):
    db.setup_database(connection)
    count = connection.execute("SELECT COUNT(*) AS n FROM choices").fetchone()["n"]
    assert count == 16
