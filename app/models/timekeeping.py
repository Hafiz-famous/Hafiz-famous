from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app import db

class TimekeepingType(db.Model):
    """Types de pointage"""
    __tablename__ = 'timekeeping_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    description = Column(Text)
    
    def __repr__(self):
        return f'<TimekeepingType {self.name}>'

class Timekeeping(db.Model):
    """Modèle pour les pointages"""
    __tablename__ = 'timekeeping'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    type = Column(String(20), nullable=False)  # 'arrival', 'departure', 'break_start', 'break_end'
    
    # Heures de pointage
    time = Column(DateTime, nullable=False)
    expected_time = Column(DateTime)  # Heure attendue selon l'horaire
    
    # Calculs automatiques
    is_late = Column(Boolean, default=False)
    late_minutes = Column(Integer, default=0)
    overtime_hours = Column(Float, default=0.0)
    
    # Informations supplémentaires
    location = Column(String(100))  # Localisation du pointage
    device = Column(String(50))     # Appareil utilisé
    notes = Column(Text)
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validated_by_id = Column(Integer, ForeignKey('users.id'))
    validated_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship('User', back_populates='timekeeping_records')
    validated_by = relationship('User', foreign_keys=[validated_by_id])
    
    def __repr__(self):
        return f'<Timekeeping {self.user.username} - {self.date.date()} {self.type}>'
    
    @hybrid_property
    def is_weekend(self):
        """Vérifie si le pointage est un weekend"""
        return self.date.weekday() >= 5
    
    @hybrid_property
    def is_holiday(self):
        """Vérifie si le pointage est un jour férié"""
        # Liste des jours fériés français (à étendre selon les besoins)
        holidays = [
            (1, 1),   # Nouvel An
            (5, 1),   # Fête du Travail
            (5, 8),   # Victoire 1945
            (7, 14),  # Fête Nationale
            (8, 15),  # Assomption
            (11, 1),  # Toussaint
            (11, 11), # Armistice
            (12, 25), # Noël
        ]
        return (self.date.month, self.date.day) in holidays
    
    def calculate_late_minutes(self):
        """Calcule les minutes de retard"""
        if not self.expected_time:
            return 0
        
        if self.time > self.expected_time:
            diff = self.time - self.expected_time
            return int(diff.total_seconds() / 60)
        return 0
    
    def calculate_overtime_hours(self):
        """Calcule les heures supplémentaires"""
        if self.type != 'departure':
            return 0.0
        
        # Heure de fin normale (17h30 par exemple)
        normal_end_time = datetime.combine(self.date.date(), datetime.strptime('17:30', '%H:%M').time())
        
        if self.time > normal_end_time:
            diff = self.time - normal_end_time
            return round(diff.total_seconds() / 3600, 2)
        
        return 0.0
    
    def validate(self, validator_id):
        """Valide le pointage"""
        self.is_validated = True
        self.validated_by_id = validator_id
        self.validated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convertit le pointage en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': {
                'id': self.user.id,
                'name': self.user.full_name,
                'employee_id': self.user.employee_id
            } if self.user else None,
            'date': self.date.isoformat(),
            'type': self.type,
            'time': self.time.isoformat(),
            'expected_time': self.expected_time.isoformat() if self.expected_time else None,
            'is_late': self.is_late,
            'late_minutes': self.late_minutes,
            'overtime_hours': self.overtime_hours,
            'location': self.location,
            'device': self.device,
            'notes': self.notes,
            'is_validated': self.is_validated,
            'validated_by': {
                'id': self.validated_by.id,
                'name': self.validated_by.full_name
            } if self.validated_by else None,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'is_weekend': self.is_weekend,
            'is_holiday': self.is_holiday,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_daily_summary(cls, user_id, date):
        """Obtient le résumé quotidien pour un utilisateur"""
        records = cls.query.filter_by(user_id=user_id, date=date).all()
        
        arrival = next((r for r in records if r.type == 'arrival'), None)
        departure = next((r for r in records if r.type == 'departure'), None)
        
        total_hours = 0
        if arrival and departure:
            diff = departure.time - arrival.time
            total_hours = round(diff.total_seconds() / 3600, 2)
        
        return {
            'date': date.isoformat(),
            'arrival': arrival.to_dict() if arrival else None,
            'departure': departure.to_dict() if departure else None,
            'total_hours': total_hours,
            'overtime_hours': sum(r.overtime_hours for r in records),
            'late_minutes': sum(r.late_minutes for r in records)
        }
    
    @classmethod
    def get_monthly_summary(cls, user_id, year, month):
        """Obtient le résumé mensuel pour un utilisateur"""
        from datetime import date
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        records = cls.query.filter(
            cls.user_id == user_id,
            cls.date >= start_date,
            cls.date <= end_date
        ).all()
        
        total_overtime = sum(r.overtime_hours for r in records)
        total_late_minutes = sum(r.late_minutes for r in records)
        working_days = len(set(r.date.date() for r in records if r.type == 'arrival'))
        
        return {
            'year': year,
            'month': month,
            'working_days': working_days,
            'total_overtime_hours': total_overtime,
            'total_late_minutes': total_late_minutes,
            'average_late_minutes': total_late_minutes / working_days if working_days > 0 else 0
        }