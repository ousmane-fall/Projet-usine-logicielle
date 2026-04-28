import logging

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskflow.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key"

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
