"""Flask application factory for Fever-Dreams."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from db import close_db


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Fever-Dreams Flask application."""
    load_dotenv()

    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=os.getenv("DATABASE_URL"),
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-me"),
    )

    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(close_db)

    @app.get("/")
    def index():
        """Render the public landing page."""
        return render_template("index.html")

    @app.get("/health")
    def health():
        """Provide a dependency-free application health check."""
        return jsonify(status="ok", application="fever-dreams")

    @app.errorhandler(404)
    def not_found(_error):
        return render_template(
            "error.html",
            title="Page not found",
            message="The page you requested does not exist.",
        ), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return render_template(
            "error.html",
            title="Something went wrong",
            message="The request could not be completed. Please try again.",
        ), 500

    # TODO: Implement the routes specified in README.md:
    # /register, /login, /logout, /dashboard, /scenarios/<id>,
    # /playthroughs, /playthroughs/<id>, and the playthrough JSON API.

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")

