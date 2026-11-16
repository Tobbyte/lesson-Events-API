# noqa: D100
import os

import yaml  # pyright: ignore[reportMissingModuleSource] # noqa: F401
from config import Config
from flask import (  # pyright: ignore[reportMissingImports]
    Flask,
    jsonify,
    send_from_directory,
)
from flask_cors import CORS  # pyright: ignore[reportMissingModuleSource]
from flask_jwt_extended import (  # pyright: ignore[reportMissingImports]
    JWTManager,
)
from flask_swagger_ui import (  # pyright: ignore[reportMissingImports]
    get_swaggerui_blueprint,
)
from models import db
from routes.auth import auth_bp
from routes.events import events_bp
from routes.rsvps import rsvps_bp


def create_app() -> Flask:  # noqa: D103
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)  # noqa: F841

    # Swagger UI configuration
    SWAGGER_URL = "/apidocs"  # noqa: N806
    API_URL = "/api/openapi.yaml"  # noqa: N806

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            "app_name": "Evently API",
        },
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Serve OpenAPI spec file
    @app.route("/api/openapi.yaml")
    def serve_openapi() -> tuple[str, int]:
        return send_from_directory(
            os.path.dirname(os.path.abspath(__file__)),  # noqa: PTH100, PTH120
            "openapi.yaml",
        )  # pyright: ignore[reportReturnType]

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(rsvps_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    # Root endpoint
    @app.route("/", methods=["GET"])
    def root() -> tuple[dict[str, str | dict[str, str]], int]:
        return jsonify({
            "name": "Evently API",
            "version": "1.0.0",
            "description": "A Flask-based REST API for managing events and RSVPs with different access levels",  # noqa: E501
            "documentation": {
                "swagger_ui": "/apidocs",
                "openapi_spec": "/api/openapi.yaml",
            },
            "endpoints": {
                "health": "/api/health",
                "auth": {
                    "register": "/api/auth/register",
                    "login": "/api/auth/login",
                },
                "events": {
                    "list": "/api/events",
                    "get": "/api/events/{id}",
                    "create": "/api/events",
                },
                "rsvps": {
                    "rsvp": "/api/rsvps/event/{event_id}",
                    "get_rsvps": "/api/rsvps/event/{event_id}",
                },
            },
        }), 200  # pyright: ignore[reportReturnType]

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health() -> tuple[dict[str, str], int]:
        return jsonify({"status": "hurtz"}), 200  # pyright: ignore[reportReturnType]

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)  # noqa: S104
