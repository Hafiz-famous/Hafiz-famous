from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app import db
from app.models.role import Role, Permission

class User(db.Model):
    """Modèle utilisateur avec gestion des rôles"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Informations professionnelles
    position = Column(String(100), nullable=False)
    hire_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    salary = Column(Float, nullable=False)
    hourly_rate = Column(Float, nullable=False)
    
    # Statut
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    
    # Relations
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    department = relationship('Department', back_populates='users')
    role = relationship('Role', back_populates='users')
    timekeeping_records = relationship('Timekeeping', back_populates='user', cascade='all, delete-orphan')
    leaves = relationship('Leave', back_populates='user', cascade='all, delete-orphan')
    leave_requests = relationship('Leave', foreign_keys='Leave.requested_by_id', back_populates='requested_by')
    approved_leaves = relationship('Leave', foreign_keys='Leave.approved_by_id', back_populates='approved_by')
    employee_of_month_nominations = relationship('EmployeeOfMonth', back_populates='nominated_by')
    employee_of_month_wins = relationship('EmployeeOfMonth', foreign_keys='EmployeeOfMonth.employee_id', back_populates='employee')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @hybrid_property
    def full_name(self):
        """Nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}"
    
    @hybrid_property
    def is_manager(self):
        """Vérifie si l'utilisateur est un manager"""
        return self.role.name in ['manager', 'admin', 'hr_manager']
    
    @hybrid_property
    def is_admin(self):
        """Vérifie si l'utilisateur est un administrateur"""
        return self.role.name in ['admin', 'hr_manager']
    
    def has_permission(self, permission_name):
        """Vérifie si l'utilisateur a une permission spécifique"""
        return permission_name in [p.name for p in self.role.permissions]
    
    def can_approve_leaves(self):
        """Vérifie si l'utilisateur peut approuver des congés"""
        return self.has_permission('approve_leaves') or self.is_manager
    
    def can_view_reports(self):
        """Vérifie si l'utilisateur peut voir les rapports"""
        return self.has_permission('view_reports') or self.is_admin
    
    def can_manage_users(self):
        """Vérifie si l'utilisateur peut gérer les utilisateurs"""
        return self.has_permission('manage_users') or self.is_admin
    
    def to_dict(self):
        """Convertit l'utilisateur en dictionnaire"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'employee_id': self.employee_id,
            'position': self.position,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'salary': self.salary,
            'hourly_rate': self.hourly_rate,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'department': {
                'id': self.department.id,
                'name': self.department.name
            } if self.department else None,
            'role': {
                'id': self.role.id,
                'name': self.role.name
            } if self.role else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_public_dict(self):
        """Convertit l'utilisateur en dictionnaire public (sans données sensibles)"""
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'employee_id': self.employee_id,
            'position': self.position,
            'department': {
                'id': self.department.id,
                'name': self.department.name
            } if self.department else None,
            'is_active': self.is_active
        }