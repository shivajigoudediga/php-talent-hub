from flask import Flask, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config
import os

db       = SQLAlchemy()
jwt      = JWTManager()
mail     = Mail()
migrate  = Migrate()
socketio = SocketIO()                          # ← NEW

def create_app(config_class=Config):
    project_root    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_folder = os.path.join(os.path.dirname(project_root), 'frontend')

    app = Flask(__name__, template_folder=frontend_folder)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(                         # ← NEW
        app,
        cors_allowed_origins="*",
        async_mode="threading"
    )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Invalid token", "error": str(error)}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired. Please log in again."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message": "Authorization token is missing", "error": str(error)}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has been revoked"}), 401

    from app.routes.auth      import auth_bp
    from app.routes.developer import developer_bp
    from app.routes.recruiter import recruiter_bp
    from app.routes.jobs      import jobs_bp
    from app.sockets          import register_socket_events   # ← NEW

    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(developer_bp, url_prefix='/api/developer')
    app.register_blueprint(recruiter_bp, url_prefix='/api/recruiter')
    app.register_blueprint(jobs_bp,      url_prefix='/api/jobs')

    register_socket_events(socketio)           # ← NEW

    @app.route('/')
    def index():
        return send_from_directory(app.template_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.template_folder, path)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    return app