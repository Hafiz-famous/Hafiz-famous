import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
import structlog

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
bcrypt = Bcrypt()

def create_app(config_name=None):
    """Factory pattern pour créer l'application Flask"""
    
    # Configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configuration du logging
    setup_logging(app)
    
    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    bcrypt.init_app(app)
    
    # Enregistrement des blueprints
    register_blueprints(app)
    
    # Configuration des handlers d'erreur
    register_error_handlers(app)
    
    # Configuration des hooks de requête
    register_request_hooks(app)
    
    # Configuration JWT
    setup_jwt_handlers()
    
    return app

def setup_logging(app):
    """Configuration du logging structuré"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=app.logger.handlers[0].stream if app.logger.handlers else None,
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    )

def register_blueprints(app):
    """Enregistrement des blueprints"""
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.departments import departments_bp
    from app.routes.timekeeping import timekeeping_bp
    from app.routes.leaves import leaves_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp
    from app.routes.employee_of_month import employee_of_month_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(departments_bp, url_prefix='/api/departments')
    app.register_blueprint(timekeeping_bp, url_prefix='/api/timekeeping')
    app.register_blueprint(leaves_bp, url_prefix='/api/leaves')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(employee_of_month_bp, url_prefix='/api/employee-of-month')
    
    # Routes web (templates)
    from app.routes.web import web_bp
    app.register_blueprint(web_bp)

def register_error_handlers(app):
    """Enregistrement des handlers d'erreur"""
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return app.send_static_file('index.html')
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return app.send_static_file('index.html')
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'error': 'File too large'}), 413

def register_request_hooks(app):
    """Configuration des hooks de requête"""
    
    @app.before_request
    def before_request():
        """Log des requêtes"""
        if not app.debug:
            app.logger.info(
                f'{request.method} {request.path} - {request.remote_addr}',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent')
                }
            )
    
    @app.after_request
    def after_request(response):
        """Ajout des headers de sécurité"""
        if hasattr(app.config, 'SECURITY_HEADERS'):
            for header, value in app.config['SECURITY_HEADERS'].items():
                response.headers[header] = value
        
        # CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

def setup_jwt_handlers():
    """Configuration des handlers JWT"""
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'message': 'The token has expired',
            'error': 'token_expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'message': 'Signature verification failed',
            'error': 'invalid_token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'description': 'Request does not contain an access token',
            'error': 'authorization_required'
        }), 401