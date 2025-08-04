from datetime import datetime
from app import db, bcrypt
from app.models.user import User
from app.models.role import Role
from app.models.department import Department

class AuthService:
    """Service pour la gestion de l'authentification et des utilisateurs"""
    
    @staticmethod
    def create_user(data):
        """Crée un nouvel utilisateur"""
        # Hashage du mot de passe
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Vérification de l'existence du département
        department = Department.query.get(data['department_id'])
        if not department:
            raise ValueError('Département non trouvé')
        
        # Vérification de l'existence du rôle
        role = Role.query.get(data['role_id'])
        if not role:
            raise ValueError('Rôle non trouvé')
        
        # Création de l'utilisateur
        user = User(
            email=data['email'],
            username=data['username'],
            password_hash=password_hash,
            first_name=data['first_name'],
            last_name=data['last_name'],
            employee_id=data['employee_id'],
            position=data['position'],
            salary=data['salary'],
            hourly_rate=data['hourly_rate'],
            department_id=data['department_id'],
            role_id=data['role_id'],
            is_verified=True  # Par défaut, on considère l'utilisateur comme vérifié
        )
        
        return user
    
    @staticmethod
    def authenticate_user(email, password):
        """Authentifie un utilisateur"""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return None
        
        if not bcrypt.check_password_hash(user.password_hash, password):
            return None
        
        if not user.is_active:
            return None
        
        # Mise à jour de la dernière connexion
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change le mot de passe d'un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Utilisateur non trouvé')
        
        if not bcrypt.check_password_hash(user.password_hash, current_password):
            raise ValueError('Mot de passe actuel incorrect')
        
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        return True
    
    @staticmethod
    def reset_password(email):
        """Demande de réinitialisation de mot de passe"""
        user = User.query.filter_by(email=email).first()
        if not user:
            return False
        
        # En production, on générerait un token et on enverrait un email
        # Pour l'instant, on simule
        return True
    
    @staticmethod
    def verify_reset_token(token):
        """Vérifie un token de réinitialisation"""
        # En production, on vérifierait le token
        # Pour l'instant, on simule
        return True
    
    @staticmethod
    def update_user_profile(user_id, data):
        """Met à jour le profil d'un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Utilisateur non trouvé')
        
        # Mise à jour des champs autorisés
        allowed_fields = ['first_name', 'last_name', 'position']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        return user
    
    @staticmethod
    def deactivate_user(user_id):
        """Désactive un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Utilisateur non trouvé')
        
        user.is_active = False
        db.session.commit()
        
        return True
    
    @staticmethod
    def activate_user(user_id):
        """Active un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Utilisateur non trouvé')
        
        user.is_active = True
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_user_statistics(user_id):
        """Obtient les statistiques d'un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Utilisateur non trouvé')
        
        from app.models.timekeeping import Timekeeping
        from app.models.leave import Leave
        from datetime import datetime, timedelta
        
        # Statistiques du mois en cours
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        # Pointages du mois
        timekeeping_records = Timekeeping.query.filter(
            Timekeeping.user_id == user_id,
            Timekeeping.date >= start_of_month
        ).all()
        
        # Congés du mois
        leaves = Leave.query.filter(
            Leave.user_id == user_id,
            Leave.start_date >= start_of_month
        ).all()
        
        # Calculs
        total_work_days = len(set(r.date.date() for r in timekeeping_records if r.type == 'arrival'))
        total_overtime_hours = sum(r.overtime_hours for r in timekeeping_records)
        total_late_minutes = sum(r.late_minutes for r in timekeeping_records)
        approved_leaves = len([l for l in leaves if l.is_approved])
        pending_leaves = len([l for l in leaves if l.is_pending])
        
        return {
            'user_id': user_id,
            'month': now.month,
            'year': now.year,
            'total_work_days': total_work_days,
            'total_overtime_hours': total_overtime_hours,
            'total_late_minutes': total_late_minutes,
            'approved_leaves': approved_leaves,
            'pending_leaves': pending_leaves,
            'attendance_rate': (total_work_days / 22) * 100 if total_work_days > 0 else 0
        }