#!/usr/bin/env python3
"""
Point d'entrée de l'application RH Platform
"""

import os
from app import create_app, db
from app.models import User, Department, Role, Permission, TimekeepingType

def create_tables():
    """Crée les tables de la base de données"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Tables créées avec succès")

def seed_data():
    """Peuple la base de données avec des données de test"""
    app = create_app()
    with app.app_context():
        # Création des permissions
        permissions = [
            {'name': 'view_users', 'description': 'Voir les utilisateurs', 'resource': 'users', 'action': 'read'},
            {'name': 'manage_users', 'description': 'Gérer les utilisateurs', 'resource': 'users', 'action': 'manage'},
            {'name': 'view_timekeeping', 'description': 'Voir les pointages', 'resource': 'timekeeping', 'action': 'read'},
            {'name': 'edit_timekeeping', 'description': 'Modifier les pointages', 'resource': 'timekeeping', 'action': 'update'},
            {'name': 'validate_timekeeping', 'description': 'Valider les pointages', 'resource': 'timekeeping', 'action': 'validate'},
            {'name': 'view_department_timekeeping', 'description': 'Voir les pointages du département', 'resource': 'timekeeping', 'action': 'read_department'},
            {'name': 'view_overtime', 'description': 'Voir les heures supplémentaires', 'resource': 'timekeeping', 'action': 'read_overtime'},
            {'name': 'view_late_report', 'description': 'Voir les rapports de retard', 'resource': 'timekeeping', 'action': 'read_late'},
            {'name': 'view_leaves', 'description': 'Voir les congés', 'resource': 'leaves', 'action': 'read'},
            {'name': 'approve_leaves', 'description': 'Approuver les congés', 'resource': 'leaves', 'action': 'approve'},
            {'name': 'manage_leaves', 'description': 'Gérer les congés', 'resource': 'leaves', 'action': 'manage'},
            {'name': 'view_reports', 'description': 'Voir les rapports', 'resource': 'reports', 'action': 'read'},
            {'name': 'view_dashboard', 'description': 'Voir le tableau de bord', 'resource': 'dashboard', 'action': 'read'},
            {'name': 'manage_employee_of_month', 'description': 'Gérer l\'employé du mois', 'resource': 'employee_of_month', 'action': 'manage'},
        ]
        
        for perm_data in permissions:
            perm = Permission.query.filter_by(name=perm_data['name']).first()
            if not perm:
                perm = Permission(**perm_data)
                db.session.add(perm)
        
        # Création des rôles
        roles = [
            {
                'name': 'employee',
                'description': 'Employé standard',
                'permissions': ['view_timekeeping', 'view_leaves']
            },
            {
                'name': 'manager',
                'description': 'Manager d\'équipe',
                'permissions': ['view_timekeeping', 'edit_timekeeping', 'validate_timekeeping', 
                              'view_department_timekeeping', 'view_overtime', 'view_late_report',
                              'view_leaves', 'approve_leaves', 'view_reports', 'view_dashboard']
            },
            {
                'name': 'hr_manager',
                'description': 'Manager RH',
                'permissions': ['view_users', 'manage_users', 'view_timekeeping', 'edit_timekeeping',
                              'validate_timekeeping', 'view_department_timekeeping', 'view_overtime',
                              'view_late_report', 'view_leaves', 'approve_leaves', 'manage_leaves',
                              'view_reports', 'view_dashboard', 'manage_employee_of_month']
            },
            {
                'name': 'admin',
                'description': 'Administrateur',
                'permissions': [p['name'] for p in permissions]
            }
        ]
        
        for role_data in roles:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                role = Role(name=role_data['name'], description=role_data['description'])
                db.session.add(role)
                db.session.flush()  # Pour obtenir l'ID du rôle
                
                # Ajout des permissions
                for perm_name in role_data['permissions']:
                    perm = Permission.query.filter_by(name=perm_name).first()
                    if perm:
                        role.permissions.append(perm)
        
        # Création des départements
        departments = [
            {'name': 'Ressources Humaines', 'code': 'RH', 'description': 'Département RH'},
            {'name': 'Développement', 'code': 'DEV', 'description': 'Département Développement'},
            {'name': 'Marketing', 'code': 'MKT', 'description': 'Département Marketing'},
            {'name': 'Finance', 'code': 'FIN', 'description': 'Département Finance'},
            {'name': 'Commercial', 'code': 'COM', 'description': 'Département Commercial'},
        ]
        
        for dept_data in departments:
            dept = Department.query.filter_by(code=dept_data['code']).first()
            if not dept:
                dept = Department(**dept_data)
                db.session.add(dept)
        
        # Création des types de pointage
        timekeeping_types = [
            {'name': 'Arrivée', 'code': 'ARR', 'description': 'Pointage d\'arrivée'},
            {'name': 'Départ', 'code': 'DEP', 'description': 'Pointage de départ'},
            {'name': 'Début pause', 'code': 'PAUSE_START', 'description': 'Début de pause'},
            {'name': 'Fin pause', 'code': 'PAUSE_END', 'description': 'Fin de pause'},
        ]
        
        for type_data in timekeeping_types:
            tt = TimekeepingType.query.filter_by(code=type_data['code']).first()
            if not tt:
                tt = TimekeepingType(**type_data)
                db.session.add(tt)
        
        db.session.commit()
        print("Données de test créées avec succès")

def create_admin_user():
    """Crée un utilisateur administrateur par défaut"""
    app = create_app()
    with app.app_context():
        from app import bcrypt
        
        # Vérifier si l'admin existe déjà
        admin = User.query.filter_by(email='admin@rh-platform.com').first()
        if admin:
            print("L'utilisateur admin existe déjà")
            return
        
        # Récupérer le rôle admin et le département RH
        admin_role = Role.query.filter_by(name='admin').first()
        rh_department = Department.query.filter_by(code='RH').first()
        
        if not admin_role or not rh_department:
            print("Rôle admin ou département RH non trouvé. Exécutez d'abord seed_data()")
            return
        
        # Créer l'utilisateur admin
        admin_user = User(
            email='admin@rh-platform.com',
            username='admin',
            password_hash=bcrypt.generate_password_hash('Admin123!').decode('utf-8'),
            first_name='Admin',
            last_name='System',
            employee_id='ADM001',
            position='Administrateur',
            salary=5000.0,
            hourly_rate=25.0,
            department_id=rh_department.id,
            role_id=admin_role.id,
            is_verified=True,
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print("Utilisateur admin créé avec succès")
        print("Email: admin@rh-platform.com")
        print("Mot de passe: Admin123!")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'create-tables':
            create_tables()
        elif command == 'seed-data':
            seed_data()
        elif command == 'create-admin':
            create_admin_user()
        elif command == 'init':
            print("Initialisation de la base de données...")
            create_tables()
            seed_data()
            create_admin_user()
            print("Initialisation terminée!")
        else:
            print("Commandes disponibles:")
            print("  create-tables  - Crée les tables de la base de données")
            print("  seed-data      - Peuple la base avec des données de test")
            print("  create-admin   - Crée un utilisateur administrateur")
            print("  init           - Initialise complètement la base de données")
    else:
        # Lancement normal de l'application
        app = create_app()
        app.run(
            host=os.environ.get('HOST', '0.0.0.0'),
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_ENV') == 'development'
        )