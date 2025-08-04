from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import enum
from app import db

class LeaveType(enum.Enum):
    """Types de congés"""
    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"
    OTHER = "other"

class LeaveStatus(enum.Enum):
    """Statuts des demandes de congés"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Leave(db.Model):
    """Modèle pour les congés"""
    __tablename__ = 'leaves'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Informations de la demande
    type = Column(Enum(LeaveType), nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    
    # Dates
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    
    # Calculs automatiques
    total_days = Column(Float, nullable=False)
    working_days = Column(Float, nullable=False)
    
    # Raison et justification
    reason = Column(Text, nullable=False)
    notes = Column(Text)
    
    # Validation
    requested_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship('User', back_populates='leaves')
    requested_by = relationship('User', foreign_keys=[requested_by_id], back_populates='leave_requests')
    approved_by = relationship('User', foreign_keys=[approved_by_id], back_populates='approved_leaves')
    
    def __repr__(self):
        return f'<Leave {self.user.username} - {self.start_date.date()} to {self.end_date.date()}>'
    
    @hybrid_property
    def is_approved(self):
        """Vérifie si le congé est approuvé"""
        return self.status == LeaveStatus.APPROVED
    
    @hybrid_property
    def is_pending(self):
        """Vérifie si le congé est en attente"""
        return self.status == LeaveStatus.PENDING
    
    @hybrid_property
    def is_rejected(self):
        """Vérifie si le congé est rejeté"""
        return self.status == LeaveStatus.REJECTED
    
    @hybrid_property
    def is_cancelled(self):
        """Vérifie si le congé est annulé"""
        return self.status == LeaveStatus.CANCELLED
    
    @hybrid_property
    def is_current(self):
        """Vérifie si le congé est en cours"""
        now = datetime.utcnow()
        return self.is_approved and self.start_date <= now <= self.end_date
    
    @hybrid_property
    def is_future(self):
        """Vérifie si le congé est dans le futur"""
        return self.start_date > datetime.utcnow()
    
    @hybrid_property
    def is_past(self):
        """Vérifie si le congé est dans le passé"""
        return self.end_date < datetime.utcnow()
    
    def calculate_days(self):
        """Calcule le nombre de jours de congé"""
        delta = self.end_date - self.start_date
        self.total_days = delta.days + 1
        
        # Calcul des jours ouvrables (excluant weekends)
        working_days = 0
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.weekday() < 5:  # Lundi à Vendredi
                working_days += 1
            current_date += timedelta(days=1)
        
        self.working_days = working_days
    
    def approve(self, approver_id, notes=None):
        """Approuve le congé"""
        self.status = LeaveStatus.APPROVED
        self.approved_by_id = approver_id
        self.approved_at = datetime.utcnow()
        if notes:
            self.notes = notes
    
    def reject(self, rejector_id, reason):
        """Rejette le congé"""
        self.status = LeaveStatus.REJECTED
        self.approved_by_id = rejector_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = reason
    
    def cancel(self, canceller_id):
        """Annule le congé"""
        self.status = LeaveStatus.CANCELLED
        self.approved_by_id = canceller_id
        self.approved_at = datetime.utcnow()
    
    def to_dict(self):
        """Convertit le congé en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': {
                'id': self.user.id,
                'name': self.user.full_name,
                'employee_id': self.user.employee_id
            } if self.user else None,
            'type': self.type.value,
            'status': self.status.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'total_days': self.total_days,
            'working_days': self.working_days,
            'reason': self.reason,
            'notes': self.notes,
            'requested_by': {
                'id': self.requested_by.id,
                'name': self.requested_by.full_name
            } if self.requested_by else None,
            'approved_by': {
                'id': self.approved_by.id,
                'name': self.approved_by.full_name
            } if self.approved_by else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'is_approved': self.is_approved,
            'is_pending': self.is_pending,
            'is_rejected': self.is_rejected,
            'is_cancelled': self.is_cancelled,
            'is_current': self.is_current,
            'is_future': self.is_future,
            'is_past': self.is_past,
            'requested_at': self.requested_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_user_leave_balance(cls, user_id, year=None):
        """Calcule le solde de congés d'un utilisateur"""
        if not year:
            year = datetime.utcnow().year
        
        # Congés annuels accordés (25 jours par défaut)
        annual_entitlement = 25
        
        # Congés pris
        taken_leaves = cls.query.filter(
            cls.user_id == user_id,
            cls.type == LeaveType.ANNUAL,
            cls.status == LeaveStatus.APPROVED,
            cls.start_date >= datetime(year, 1, 1),
            cls.end_date <= datetime(year, 12, 31)
        ).all()
        
        taken_days = sum(leave.working_days for leave in taken_leaves)
        
        return {
            'year': year,
            'entitlement': annual_entitlement,
            'taken': taken_days,
            'remaining': annual_entitlement - taken_days,
            'leaves': [leave.to_dict() for leave in taken_leaves]
        }
    
    @classmethod
    def get_department_leaves(cls, department_id, start_date=None, end_date=None):
        """Obtient les congés d'un département"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow() + timedelta(days=30)
        
        from app.models.user import User
        
        leaves = cls.query.join(User).filter(
            User.department_id == department_id,
            cls.start_date >= start_date,
            cls.end_date <= end_date
        ).all()
        
        return [leave.to_dict() for leave in leaves]