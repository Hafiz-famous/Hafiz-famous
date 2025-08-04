from marshmallow import Schema, fields, validate, ValidationError
import re

class LoginSchema(Schema):
    """Schéma de validation pour la connexion"""
    email = fields.Email(required=True, error_messages={
        'required': 'L\'email est requis',
        'invalid': 'Format d\'email invalide'
    })
    password = fields.Str(required=True, validate=validate.Length(min=6), error_messages={
        'required': 'Le mot de passe est requis',
        'validator_failed': 'Le mot de passe doit contenir au moins 6 caractères'
    })

class RegisterSchema(Schema):
    """Schéma de validation pour l'inscription"""
    email = fields.Email(required=True, error_messages={
        'required': 'L\'email est requis',
        'invalid': 'Format d\'email invalide'
    })
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50), error_messages={
        'required': 'Le nom d\'utilisateur est requis',
        'validator_failed': 'Le nom d\'utilisateur doit contenir entre 3 et 50 caractères'
    })
    password = fields.Str(required=True, validate=validate.Length(min=8), error_messages={
        'required': 'Le mot de passe est requis',
        'validator_failed': 'Le mot de passe doit contenir au moins 8 caractères'
    })
    confirm_password = fields.Str(required=True, error_messages={
        'required': 'La confirmation du mot de passe est requise'
    })
    first_name = fields.Str(required=True, validate=validate.Length(min=2, max=50), error_messages={
        'required': 'Le prénom est requis',
        'validator_failed': 'Le prénom doit contenir entre 2 et 50 caractères'
    })
    last_name = fields.Str(required=True, validate=validate.Length(min=2, max=50), error_messages={
        'required': 'Le nom est requis',
        'validator_failed': 'Le nom doit contenir entre 2 et 50 caractères'
    })
    employee_id = fields.Str(required=True, validate=validate.Length(min=3, max=20), error_messages={
        'required': 'L\'ID employé est requis',
        'validator_failed': 'L\'ID employé doit contenir entre 3 et 20 caractères'
    })
    position = fields.Str(required=True, validate=validate.Length(min=2, max=100), error_messages={
        'required': 'Le poste est requis',
        'validator_failed': 'Le poste doit contenir entre 2 et 100 caractères'
    })
    salary = fields.Float(required=True, validate=validate.Range(min=0), error_messages={
        'required': 'Le salaire est requis',
        'validator_failed': 'Le salaire doit être positif'
    })
    hourly_rate = fields.Float(required=True, validate=validate.Range(min=0), error_messages={
        'required': 'Le taux horaire est requis',
        'validator_failed': 'Le taux horaire doit être positif'
    })
    department_id = fields.Int(required=True, error_messages={
        'required': 'Le département est requis',
        'invalid': 'L\'ID du département doit être un nombre entier'
    })
    role_id = fields.Int(required=True, error_messages={
        'required': 'Le rôle est requis',
        'invalid': 'L\'ID du rôle doit être un nombre entier'
    })
    
    def validate_password(self, data):
        """Validation personnalisée du mot de passe"""
        password = data.get('password')
        if password:
            # Vérification de la complexité du mot de passe
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une majuscule')
            if not re.search(r'[a-z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une minuscule')
            if not re.search(r'\d', password):
                raise ValidationError('Le mot de passe doit contenir au moins un chiffre')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('Le mot de passe doit contenir au moins un caractère spécial')
    
    def validate_confirm_password(self, data):
        """Validation de la confirmation du mot de passe"""
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Les mots de passe ne correspondent pas')
    
    def validate_employee_id(self, data):
        """Validation de l'ID employé"""
        employee_id = data.get('employee_id')
        if employee_id:
            # Vérification du format (ex: EMP001)
            if not re.match(r'^[A-Z]{2,3}\d{3,6}$', employee_id):
                raise ValidationError('L\'ID employé doit suivre le format EMP001')

class ChangePasswordSchema(Schema):
    """Schéma de validation pour le changement de mot de passe"""
    current_password = fields.Str(required=True, error_messages={
        'required': 'Le mot de passe actuel est requis'
    })
    new_password = fields.Str(required=True, validate=validate.Length(min=8), error_messages={
        'required': 'Le nouveau mot de passe est requis',
        'validator_failed': 'Le nouveau mot de passe doit contenir au moins 8 caractères'
    })
    confirm_password = fields.Str(required=True, error_messages={
        'required': 'La confirmation du nouveau mot de passe est requise'
    })
    
    def validate_new_password(self, data):
        """Validation personnalisée du nouveau mot de passe"""
        password = data.get('new_password')
        if password:
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une majuscule')
            if not re.search(r'[a-z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une minuscule')
            if not re.search(r'\d', password):
                raise ValidationError('Le mot de passe doit contenir au moins un chiffre')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('Le mot de passe doit contenir au moins un caractère spécial')
    
    def validate_confirm_password(self, data):
        """Validation de la confirmation du mot de passe"""
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('Les mots de passe ne correspondent pas')

class ForgotPasswordSchema(Schema):
    """Schéma de validation pour la demande de réinitialisation"""
    email = fields.Email(required=True, error_messages={
        'required': 'L\'email est requis',
        'invalid': 'Format d\'email invalide'
    })

class ResetPasswordSchema(Schema):
    """Schéma de validation pour la réinitialisation de mot de passe"""
    token = fields.Str(required=True, error_messages={
        'required': 'Le token est requis'
    })
    new_password = fields.Str(required=True, validate=validate.Length(min=8), error_messages={
        'required': 'Le nouveau mot de passe est requis',
        'validator_failed': 'Le nouveau mot de passe doit contenir au moins 8 caractères'
    })
    confirm_password = fields.Str(required=True, error_messages={
        'required': 'La confirmation du nouveau mot de passe est requise'
    })
    
    def validate_new_password(self, data):
        """Validation personnalisée du nouveau mot de passe"""
        password = data.get('new_password')
        if password:
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une majuscule')
            if not re.search(r'[a-z]', password):
                raise ValidationError('Le mot de passe doit contenir au moins une minuscule')
            if not re.search(r'\d', password):
                raise ValidationError('Le mot de passe doit contenir au moins un chiffre')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('Le mot de passe doit contenir au moins un caractère spécial')
    
    def validate_confirm_password(self, data):
        """Validation de la confirmation du mot de passe"""
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('Les mots de passe ne correspondent pas')