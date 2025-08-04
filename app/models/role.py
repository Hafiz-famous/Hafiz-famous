from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, Text
from sqlalchemy.orm import relationship
from app import db

# Table d'association pour les permissions des rôles
role_permissions = Table(
    'role_permissions',
    db.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class Role(db.Model):
    """Modèle pour les rôles utilisateur"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_active = Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    users = relationship('User', back_populates='role')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def to_dict(self):
        """Convertit le rôle en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'permissions': [p.name for p in self.permissions],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Permission(db.Model):
    """Modèle pour les permissions"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    resource = Column(String(100), nullable=False)  # Ressource concernée (users, leaves, etc.)
    action = Column(String(50), nullable=False)     # Action (create, read, update, delete)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        """Convertit la permission en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }