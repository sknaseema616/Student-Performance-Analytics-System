from flask import Flask
from flask_jwt_extended import JWTManager
from app.auth import auth_bp
from app.routes import routes_bp
from app.api import api_bp
from app.analytics import analytics_bp
from app.method_override import init_method_override
def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    app.config["SECRET_KEY"] = "student-performance-secret-key"
    app.config["JWT_SECRET_KEY"] = "student-performance-jwt-secret-key"
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 900
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 604800
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_COOKIE_HTTPONLY"] = True
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    JWTManager(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(analytics_bp)
    init_method_override(app)
    return app