from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.department import Department
from app.models.timekeeping import Timekeeping
from app.models.leave import Leave
from app.models.employee_of_month import EmployeeOfMonth
from datetime import datetime

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@web_bp.route('/login')
def login():
    """Page de connexion"""
    return render_template('auth/login.html')

@web_bp.route('/dashboard')
@jwt_required()
def dashboard():
    """Tableau de bord principal"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    # Statistiques du jour
    today = datetime.utcnow().date()
    today_records = Timekeeping.query.filter_by(
        user_id=current_user_id,
        date=today
    ).all()
    
    # Congés en cours
    current_leaves = Leave.query.filter_by(
        user_id=current_user_id,
        status='approved'
    ).filter(
        Leave.start_date <= datetime.utcnow(),
        Leave.end_date >= datetime.utcnow()
    ).all()
    
    # Employé du mois actuel
    current_employee = EmployeeOfMonth.get_current_employee_of_month()
    
    return render_template('dashboard/index.html', 
                         user=user,
                         today_records=today_records,
                         current_leaves=current_leaves,
                         current_employee=current_employee)

@web_bp.route('/timekeeping')
@jwt_required()
def timekeeping():
    """Page de pointage"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    # Pointages du jour
    today = datetime.utcnow().date()
    today_records = Timekeeping.query.filter_by(
        user_id=current_user_id,
        date=today
    ).order_by(Timekeeping.time).all()
    
    # Historique des 7 derniers jours
    from datetime import timedelta
    week_ago = today - timedelta(days=7)
    week_records = Timekeeping.query.filter(
        Timekeeping.user_id == current_user_id,
        Timekeeping.date >= week_ago
    ).order_by(Timekeeping.date.desc(), Timekeeping.time.desc()).all()
    
    return render_template('timekeeping/index.html',
                         user=user,
                         today_records=today_records,
                         week_records=week_records)

@web_bp.route('/leaves')
@jwt_required()
def leaves():
    """Page de gestion des congés"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    # Congés de l'utilisateur
    user_leaves = Leave.query.filter_by(user_id=current_user_id).order_by(Leave.start_date.desc()).all()
    
    # Congés à approuver (si manager)
    pending_leaves = []
    if user.can_approve_leaves():
        pending_leaves = Leave.query.filter_by(status='pending').order_by(Leave.requested_at.desc()).all()
    
    return render_template('leaves/index.html',
                         user=user,
                         user_leaves=user_leaves,
                         pending_leaves=pending_leaves)

@web_bp.route('/reports')
@jwt_required()
def reports():
    """Page des rapports"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    if not user.can_view_reports():
        flash('Vous n\'avez pas les permissions pour accéder aux rapports', 'error')
        return redirect(url_for('web.dashboard'))
    
    # Statistiques par département
    departments = Department.query.filter_by(is_active=True).all()
    
    return render_template('reports/index.html',
                         user=user,
                         departments=departments)

@web_bp.route('/employee-of-month')
@jwt_required()
def employee_of_month():
    """Page de l'employé du mois"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    # Employé du mois actuel
    current_employee = EmployeeOfMonth.get_current_employee_of_month()
    
    # Historique des employés du mois
    history = EmployeeOfMonth.get_employee_of_month_history(limit=12)
    
    return render_template('employee_of_month/index.html',
                         user=user,
                         current_employee=current_employee,
                         history=history)

@web_bp.route('/profile')
@jwt_required()
def profile():
    """Page de profil utilisateur"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    # Statistiques de l'utilisateur
    from app.services.auth_service import AuthService
    stats = AuthService.get_user_statistics(current_user_id)
    
    return render_template('profile/index.html',
                         user=user,
                         stats=stats)

@web_bp.route('/admin')
@jwt_required()
def admin():
    """Page d'administration"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    if not user.is_admin:
        flash('Vous n\'avez pas les permissions pour accéder à l\'administration', 'error')
        return redirect(url_for('web.dashboard'))
    
    # Statistiques globales
    total_users = User.query.filter_by(is_active=True).count()
    total_departments = Department.query.filter_by(is_active=True).count()
    
    # Pointages du jour
    today = datetime.utcnow().date()
    today_punches = Timekeeping.query.filter_by(date=today).count()
    
    # Congés en attente
    pending_leaves = Leave.query.filter_by(status='pending').count()
    
    return render_template('admin/index.html',
                         user=user,
                         total_users=total_users,
                         total_departments=total_departments,
                         today_punches=today_punches,
                         pending_leaves=pending_leaves)

@web_bp.route('/users')
@jwt_required()
def users():
    """Page de gestion des utilisateurs"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    if not user.can_manage_users():
        flash('Vous n\'avez pas les permissions pour gérer les utilisateurs', 'error')
        return redirect(url_for('web.dashboard'))
    
    # Liste des utilisateurs
    users_list = User.query.filter_by(is_active=True).order_by(User.last_name).all()
    departments = Department.query.filter_by(is_active=True).all()
    
    return render_template('admin/users.html',
                         user=user,
                         users=users_list,
                         departments=departments)

@web_bp.route('/departments')
@jwt_required()
def departments():
    """Page de gestion des départements"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return redirect(url_for('web.login'))
    
    if not user.is_admin:
        flash('Vous n\'avez pas les permissions pour gérer les départements', 'error')
        return redirect(url_for('web.dashboard'))
    
    # Liste des départements
    departments_list = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    
    return render_template('admin/departments.html',
                         user=user,
                         departments=departments_list)