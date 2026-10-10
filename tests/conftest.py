"""Shared test setup.

Database tests need a SEPARATE, throwaway database named in TEST_DATABASE_URL
(in .env or your terminal). Every table in it is deleted before each test.
Without TEST_DATABASE_URL, those tests are skipped.
"""

import os

import pytest
from dotenv import load_dotenv

import db
import game

load_dotenv()


@pytest.fixture()
def connection():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run database tests.")

    conn = db.connect(url)
    # Start from empty tables every time so tests don't affect each other.
    conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    db.setup_database(conn)
    yield conn
    conn.close()


@pytest.fixture()
def player(connection):
    return game.get_or_create_player(connection, "tester")


@pytest.fixture()
def playthrough_id(connection, player):
    scenario = game.list_scenarios(connection)[0]
    return game.start_playthrough(connection, player["id"], scenario["id"])
