import logging
from flask import Flask, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from db import init_db
from security.headers import apply_security_headers

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Database
    init_db(app)

    # Blueprints
    from routes.tasks import tasks_bp
    app.register_blueprint(tasks_bp)

    # Apply rate limits to mutating endpoints
    limiter.limit("30 per minute")(tasks_bp)

    # Security headers on every response
    app.after_request(apply_security_headers)

    # -----------------------------------------------------------------
    # Error handlers — never reveal internal details to the client
    # -----------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request."}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def request_too_large(e):
        return jsonify({"error": "Request body too large."}), 413

    @app.errorhandler(415)
    def unsupported_media_type(e):
        return jsonify({"error": "Unsupported media type."}), 415

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Too many requests. Please slow down."}), 429

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return jsonify({"error": "CSRF validation failed."}), 400

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.exception("Internal server error")
        return jsonify({"error": "Internal server error."}), 500

    # Page route — serves the single-page UI
    @app.route("/")
    def index():
        from flask import render_template
        return render_template("index.html")

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application = create_app()
    application.run(debug=False, host="127.0.0.1", port=5000)
