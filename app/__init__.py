import logging
import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _resolve_secret_key():
    """Récupère SECRET_KEY depuis l'environnement.

    En production (FLASK_ENV=production), la variable est obligatoire.
    En dev/test, une valeur par défaut non sensible est utilisée.
    """
    secret = os.environ.get("SECRET_KEY")
    if secret:
        return secret
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError(
            "SECRET_KEY est obligatoire en production "
            "(définir la variable d'environnement SECRET_KEY)."
        )
    return "dev-secret-key"


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///taskflow.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = _resolve_secret_key()

    if config:
        app.config.update(config)

    logging.basicConfig(
        level=logging.INFO,
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    )

    db.init_app(app)

    if not app.config.get("TESTING"):
        from prometheus_flask_exporter import PrometheusMetrics
        PrometheusMetrics(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    with app.app_context():
        from app.api import api_bp
        app.register_blueprint(api_bp, url_prefix="/api")
        db.create_all()

    return app
