"""PostgreSQL connection helpers for Fever-Dreams."""

from __future__ import annotations

import psycopg
from flask import current_app, g
from psycopg.rows import dict_row


def get_db() -> psycopg.Connection:
    """Return one PostgreSQL connection for the current Flask request."""
    if "db" not in g:
        database_url = current_app.config.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured")

        g.db = psycopg.connect(database_url, row_factory=dict_row)

    return g.db


def close_db(_error: BaseException | None = None) -> None:
    """Close the request-scoped PostgreSQL connection, if one exists."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()

