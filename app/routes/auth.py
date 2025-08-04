from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash
from app import db, bcrypt
from app.models.user import User
from app.schemas.auth import LoginSchema, RegisterSchema
from app.services.auth_service import AuthService
from app.decorators import validate_json, handle_errors

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@validate_json(LoginSchema)
@handle_errors
def login():
    """Authentification utilisateur"""
    data = request.get_json()
    
    # Recherche de l'utilisateur
    user = User.query.filter_by(email=data['email']).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({
            'error': 'Invalid credentials',
            'message': 'Email ou mot de passe incorrect'
        }), 401
    
    # Vérification du statut actif
    if not user.is_active:
        return jsonify({
            'error': 'Account disabled',
            'message': 'Compte désactivé'
        }), 403
    
    # Mise à jour de la dernière connexion
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Création des tokens
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'email': user.email,
            'role': user.role.name,
            'permissions': [p.name for p in user.role.permissions]
        }
    )
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'Connexion réussie',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_public_dict(),
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
    }), 200

@auth_bp.route('/register', methods=['POST'])
@validate_json(RegisterSchema)
@handle_errors
def register():
    """Inscription d'un nouvel utilisateur"""
    data = request.get_json()
    
    # Vérification de l'unicité de l'email
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'error': 'Email already exists',
            'message': 'Cet email est déjà utilisé'
        }), 409
    
    # Vérification de l'unicité du nom d'utilisateur
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            'error': 'Username already exists',
            'message': 'Ce nom d\'utilisateur est déjà utilisé'
        }), 409
    
    # Vérification de l'unicité de l'ID employé
    if User.query.filter_by(employee_id=data['employee_id']).first():
        return jsonify({
            'error': 'Employee ID already exists',
            'message': 'Cet ID employé est déjà utilisé'
        }), 409
    
    # Création de l'utilisateur
    try:
        user = AuthService.create_user(data)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Utilisateur créé avec succès',
            'user': user.to_public_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Registration failed',
            'message': str(e)
        }), 400

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Rafraîchissement du token d'accès"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({
            'error': 'Invalid token',
            'message': 'Token invalide'
        }), 401
    
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'email': user.email,
            'role': user.role.name,
            'permissions': [p.name for p in user.role.permissions]
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Déconnexion utilisateur"""
    # En production, on pourrait ajouter le token à une liste noire
    return jsonify({
        'message': 'Déconnexion réussie'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtient les informations de l'utilisateur connecté"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({
            'error': 'User not found',
            'message': 'Utilisateur non trouvé'
        }), 404
    
    return jsonify({
        'user': user.to_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@handle_errors
def change_password():
    """Changement de mot de passe"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({
            'error': 'User not found',
            'message': 'Utilisateur non trouvé'
        }), 404
    
    data = request.get_json()
    
    # Vérification de l'ancien mot de passe
    if not bcrypt.check_password_hash(user.password_hash, data['current_password']):
        return jsonify({
            'error': 'Invalid current password',
            'message': 'Mot de passe actuel incorrect'
        }), 400
    
    # Vérification de la cohérence des nouveaux mots de passe
    if data['new_password'] != data['confirm_password']:
        return jsonify({
            'error': 'Passwords do not match',
            'message': 'Les mots de passe ne correspondent pas'
        }), 400
    
    # Mise à jour du mot de passe
    user.password_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
    db.session.commit()
    
    return jsonify({
        'message': 'Mot de passe modifié avec succès'
    }), 200

@auth_bp.route('/forgot-password', methods=['POST'])
@handle_errors
def forgot_password():
    """Demande de réinitialisation de mot de passe"""
    data = request.get_json()
    
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe
        return jsonify({
            'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'
        }), 200
    
    # En production, on enverrait un email avec un token de réinitialisation
    # Pour l'instant, on simule l'envoi
    return jsonify({
        'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'
    }), 200

@auth_bp.route('/reset-password', methods=['POST'])
@handle_errors
def reset_password():
    """Réinitialisation de mot de passe avec token"""
    data = request.get_json()
    
    # En production, on vérifierait le token
    # Pour l'instant, on simule la réinitialisation
    return jsonify({
        'message': 'Mot de passe réinitialisé avec succès'
    }), 200