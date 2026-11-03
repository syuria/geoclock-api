"""Application factory.

create_app() builds a fresh Flask app. Tests call it with a test config;
production calls it with settings from environment variables.
"""
from flask import Flask, jsonify

from .config import Config
from .extensions import db, init_redis, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    init_redis(app)

    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from .cli import seed
    app.cli.add_command(seed)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    # Return JSON (not HTML) for errors, so mobile and web clients can parse them.
    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(error="not found"), 404

    @app.errorhandler(500)
    def server_error(_e):
        # Details go to the logs, never to the client.
        return jsonify(error="internal server error"), 500

    return app
