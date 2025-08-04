from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app import db

class Department(db.Model):
    """Modèle pour les départements"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Budget et coûts
    budget = Column(Float, default=0.0)
    cost_center = Column(String(50))
    
    # Manager du département
    manager_id = Column(Integer, db.ForeignKey('users.id'))
    
    # Statut
    is_active = Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    users = relationship('User', back_populates='department')
    manager = relationship('User', foreign_keys=[manager_id])
    
    def __repr__(self):
        return f'<Department {self.name}>'
    
    @hybrid_property
    def employee_count(self):
        """Nombre d'employés dans le département"""
        return len([u for u in self.users if u.is_active])
    
    @hybrid_property
    def total_salary_cost(self):
        """Coût total des salaires du département"""
        return sum(u.salary for u in self.users if u.is_active)
    
    @hybrid_property
    def average_salary(self):
        """Salaire moyen du département"""
        active_users = [u for u in self.users if u.is_active]
        if not active_users:
            return 0.0
        return sum(u.salary for u in active_users) / len(active_users)
    
    def get_attendance_rate(self, start_date=None, end_date=None):
        """Taux de présence du département"""
        from app.models.timekeeping import Timekeeping
        from datetime import datetime, timedelta
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Calcul du taux de présence
        total_expected_days = len([u for u in self.users if u.is_active]) * 22  # 22 jours ouvrables par mois
        actual_days = db.session.query(Timekeeping).join(User).filter(
            User.department_id == self.id,
            Timekeeping.date >= start_date,
            Timekeeping.date <= end_date,
            Timekeeping.type == 'arrival'
        ).count()
        
        if total_expected_days == 0:
            return 0.0
        
        return (actual_days / total_expected_days) * 100
    
    def get_overtime_hours(self, start_date=None, end_date=None):
        """Heures supplémentaires du département"""
        from app.models.timekeeping import Timekeeping
        from datetime import datetime, timedelta
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Calcul des heures supplémentaires
        records = db.session.query(Timekeeping).join(User).filter(
            User.department_id == self.id,
            Timekeeping.date >= start_date,
            Timekeeping.date <= end_date
        ).all()
        
        total_overtime = 0
        for record in records:
            if record.overtime_hours:
                total_overtime += record.overtime_hours
        
        return total_overtime
    
    def to_dict(self):
        """Convertit le département en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'budget': self.budget,
            'cost_center': self.cost_center,
            'manager': {
                'id': self.manager.id,
                'name': self.manager.full_name
            } if self.manager else None,
            'employee_count': self.employee_count,
            'total_salary_cost': self.total_salary_cost,
            'average_salary': self.average_salary,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }