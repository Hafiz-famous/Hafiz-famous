from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from app import db
from sqlalchemy.ext.hybrid import hybrid_property

class EmployeeOfMonth(db.Model):
    """Modèle pour l'employé du mois"""
    __tablename__ = 'employee_of_month'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Période
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    
    # Critères de sélection
    attendance_rate = Column(Float, nullable=False)  # Taux de présence
    punctuality_score = Column(Float, nullable=False)  # Score de ponctualité
    performance_score = Column(Float, nullable=False)  # Score de performance
    teamwork_score = Column(Float, nullable=False)  # Score de travail d'équipe
    initiative_score = Column(Float, nullable=False)  # Score d'initiative
    
    # Score total
    total_score = Column(Float, nullable=False)
    
    # Raison de la nomination
    nomination_reason = Column(Text, nullable=False)
    achievements = Column(Text)  # Réalisations spécifiques
    
    # Nomination
    nominated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    nominated_at = Column(DateTime, default=datetime.utcnow)
    
    # Validation
    is_approved = Column(Boolean, default=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    
    # Récompense
    reward_amount = Column(Float, default=0.0)
    reward_description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    employee = relationship('User', foreign_keys=[employee_id], back_populates='employee_of_month_wins')
    nominated_by = relationship('User', foreign_keys=[nominated_by_id], back_populates='employee_of_month_nominations')
    approved_by = relationship('User', foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f'<EmployeeOfMonth {self.employee.username} - {self.year}/{self.month:02d}>'
    
    @hybrid_property
    def is_current_month(self):
        """Vérifie si c'est l'employé du mois actuel"""
        now = datetime.utcnow()
        return self.year == now.year and self.month == now.month
    
    @hybrid_property
    def period_label(self):
        """Label de la période (ex: "Janvier 2024")"""
        months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        return f"{months[self.month - 1]} {self.year}"
    
    def calculate_total_score(self):
        """Calcule le score total pondéré"""
        # Pondération des critères
        weights = {
            'attendance': 0.25,
            'punctuality': 0.20,
            'performance': 0.25,
            'teamwork': 0.15,
            'initiative': 0.15
        }
        
        self.total_score = (
            self.attendance_rate * weights['attendance'] +
            self.punctuality_score * weights['punctuality'] +
            self.performance_score * weights['performance'] +
            self.teamwork_score * weights['teamwork'] +
            self.initiative_score * weights['initiative']
        )
    
    def approve(self, approver_id):
        """Approuve la nomination"""
        self.is_approved = True
        self.approved_by_id = approver_id
        self.approved_at = datetime.utcnow()
    
    def to_dict(self):
        """Convertit l'employé du mois en dictionnaire"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee': {
                'id': self.employee.id,
                'name': self.employee.full_name,
                'employee_id': self.employee.employee_id,
                'position': self.employee.position,
                'department': {
                    'id': self.employee.department.id,
                    'name': self.employee.department.name
                } if self.employee.department else None
            } if self.employee else None,
            'year': self.year,
            'month': self.month,
            'period_label': self.period_label,
            'attendance_rate': self.attendance_rate,
            'punctuality_score': self.punctuality_score,
            'performance_score': self.performance_score,
            'teamwork_score': self.teamwork_score,
            'initiative_score': self.initiative_score,
            'total_score': self.total_score,
            'nomination_reason': self.nomination_reason,
            'achievements': self.achievements,
            'nominated_by': {
                'id': self.nominated_by.id,
                'name': self.nominated_by.full_name
            } if self.nominated_by else None,
            'nominated_at': self.nominated_at.isoformat(),
            'is_approved': self.is_approved,
            'approved_by': {
                'id': self.approved_by.id,
                'name': self.approved_by.full_name
            } if self.approved_by else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'reward_amount': self.reward_amount,
            'reward_description': self.reward_description,
            'is_current_month': self.is_current_month,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_current_employee_of_month(cls):
        """Obtient l'employé du mois actuel"""
        now = datetime.utcnow()
        return cls.query.filter_by(
            year=now.year,
            month=now.month,
            is_approved=True
        ).first()
    
    @classmethod
    def get_employee_of_month_history(cls, limit=12):
        """Obtient l'historique des employés du mois"""
        return cls.query.filter_by(is_approved=True).order_by(
            cls.year.desc(),
            cls.month.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_department_employees_of_month(cls, department_id, limit=12):
        """Obtient les employés du mois par département"""
        from app.models.user import User
        
        return cls.query.join(User).filter(
            User.department_id == department_id,
            cls.is_approved == True
        ).order_by(
            cls.year.desc(),
            cls.month.desc()
        ).limit(limit).all()
    
    @classmethod
    def calculate_employee_scores(cls, user_id, year, month):
        """Calcule les scores d'un employé pour une période donnée"""
        from app.models.timekeeping import Timekeeping
        from datetime import date
        
        # Calcul du taux de présence
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Pointages du mois
        timekeeping_records = Timekeeping.query.filter(
            Timekeeping.user_id == user_id,
            Timekeeping.date >= start_date,
            Timekeeping.date <= end_date
        ).all()
        
        # Calcul du taux de présence (22 jours ouvrables par mois)
        working_days = 22
        present_days = len(set(r.date.date() for r in timekeeping_records if r.type == 'arrival'))
        attendance_rate = (present_days / working_days) * 100 if working_days > 0 else 0
        
        # Calcul du score de ponctualité
        late_records = [r for r in timekeeping_records if r.is_late]
        total_late_minutes = sum(r.late_minutes for r in late_records)
        punctuality_score = max(0, 100 - (total_late_minutes / working_days)) if working_days > 0 else 100
        
        # Scores par défaut (à remplacer par des évaluations réelles)
        performance_score = 85.0  # Score de performance (à calculer selon les métriques)
        teamwork_score = 90.0     # Score de travail d'équipe
        initiative_score = 88.0    # Score d'initiative
        
        return {
            'attendance_rate': round(attendance_rate, 2),
            'punctuality_score': round(punctuality_score, 2),
            'performance_score': performance_score,
            'teamwork_score': teamwork_score,
            'initiative_score': initiative_score
        }