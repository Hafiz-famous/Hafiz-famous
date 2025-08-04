from functools import wraps
from flask import request, jsonify, current_app
from marshmallow import ValidationError
from app import limiter

def validate_json(schema_class):
    """Décorateur pour valider le JSON avec un schéma Marshmallow"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Content-Type must be application/json',
                    'message': 'Le contenu doit être au format JSON'
                }), 400
            
            try:
                schema = schema_class()
                data = schema.load(request.get_json())
                request.validated_data = data
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify({
                    'error': 'Validation error',
                    'message': 'Erreur de validation',
                    'details': e.messages
                }), 400
        return decorated_function
    return decorator

def handle_errors(f):
    """Décorateur pour gérer les erreurs de manière centralisée"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Log de l'erreur
            current_app.logger.error(f'Error in {f.__name__}: {str(e)}')
            
            return jsonify({
                'error': 'Internal server error',
                'message': 'Erreur interne du serveur'
            }), 500
    return decorated_function

def require_permission(permission_name):
    """Décorateur pour vérifier les permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import get_jwt_identity
            from app.models.user import User
            
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({
                    'error': 'User not found',
                    'message': 'Utilisateur non trouvé'
                }), 404
            
            if not user.has_permission(permission_name):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': 'Permissions insuffisantes'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role_name):
    """Décorateur pour vérifier le rôle"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import get_jwt_identity
            from app.models.user import User
            
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({
                    'error': 'User not found',
                    'message': 'Utilisateur non trouvé'
                }), 404
            
            if user.role.name != role_name:
                return jsonify({
                    'error': 'Insufficient role',
                    'message': f'Rôle {role_name} requis'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(limit_string):
    """Décorateur pour limiter le taux de requêtes"""
    def decorator(f):
        @limiter.limit(limit_string)
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def paginate(f):
    """Décorateur pour la pagination"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Limitation du nombre d'éléments par page
        if per_page > 100:
            per_page = 100
        
        request.page = page
        request.per_page = per_page
        
        return f(*args, **kwargs)
    return decorated_function

def cache_response(timeout=300):
    """Décorateur pour mettre en cache les réponses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # En production, on utiliserait Redis ou un autre système de cache
            # Pour l'instant, on simule le cache
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_activity(activity_type):
    """Décorateur pour logger les activités"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import get_jwt_identity
            from app.models.user import User
            
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            # Log de l'activité
            current_app.logger.info(f'Activity: {activity_type} by user {user.username if user else "unknown"}')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator