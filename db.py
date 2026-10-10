"""Connecting to PostgreSQL and setting up the tables."""

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

# The folder this file lives in, so we can find schema.sql and seed.sql.
PROJECT_FOLDER = Path(__file__).parent


def connect(database_url=None):
    """Open a connection to PostgreSQL.

    The address comes from DATABASE_URL in your .env file, for example:
    postgresql://fever_dreams:your-password@localhost:5432/fever_dreams

    dict_row makes each row a dictionary, so you can write row["title"].
    autocommit=True saves each statement right away; game.py groups
    statements that must succeed together with connection.transaction().
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")

    return psycopg.connect(database_url, row_factory=dict_row, autocommit=True)


def run_sql_file(connection, filename):
    """Run every SQL statement in a file, like schema.sql or seed.sql."""
    sql = (PROJECT_FOLDER / filename).read_text(encoding="utf-8")
    connection.execute(sql)


def setup_database(connection):
    """Create the tables (only the first time) and load the storm scenario."""
    row = connection.execute(
        "SELECT to_regclass('public.users') IS NOT NULL AS tables_exist"
    ).fetchone()

    if not row["tables_exist"]:
        run_sql_file(connection, "schema.sql")

    # seed.sql is safe to run again; it updates the content instead of duplicating it.
    run_sql_file(connection, "seed.sql")
