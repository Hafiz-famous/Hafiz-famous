from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.timekeeping import Timekeeping
from app.models.user import User
from app.schemas.timekeeping import TimekeepingCreateSchema
from app.decorators import validate_json, handle_errors, require_permission, paginate
from app.services.timekeeping_service import TimekeepingService

timekeeping_bp = Blueprint('timekeeping', __name__)

@timekeeping_bp.route('/punch', methods=['POST'])
@jwt_required()
@validate_json(TimekeepingCreateSchema)
@handle_errors
@log_activity('timekeeping_punch')
def punch_in_out():
    """Pointage arrivée/départ"""
    current_user_id = get_jwt_identity()
    data = request.validated_data
    
    # Vérification que l'utilisateur existe
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({
            'error': 'User not found',
            'message': 'Utilisateur non trouvé'
        }), 404
    
    # Création du pointage
    try:
        timekeeping = TimekeepingService.create_punch(
            user_id=current_user_id,
            punch_type=data['type'],
            location=data.get('location'),
            device=data.get('device'),
            notes=data.get('notes')
        )
        
        return jsonify({
            'message': 'Pointage enregistré avec succès',
            'timekeeping': timekeeping.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'error': 'Invalid punch',
            'message': str(e)
        }), 400

@timekeeping_bp.route('/today', methods=['GET'])
@jwt_required()
@handle_errors
def get_today_records():
    """Obtient les pointages du jour pour l'utilisateur connecté"""
    current_user_id = get_jwt_identity()
    today = datetime.utcnow().date()
    
    records = Timekeeping.query.filter_by(
        user_id=current_user_id,
        date=today
    ).order_by(Timekeeping.time).all()
    
    return jsonify({
        'date': today.isoformat(),
        'records': [record.to_dict() for record in records],
        'summary': Timekeeping.get_daily_summary(current_user_id, today)
    }), 200

@timekeeping_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
@require_permission('view_timekeeping')
@handle_errors
@paginate
def get_user_records(user_id, page=1, per_page=20):
    """Obtient les pointages d'un utilisateur"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Timekeeping.query.filter_by(user_id=user_id)
    
    if start_date:
        query = query.filter(Timekeeping.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Timekeeping.date <= datetime.fromisoformat(end_date))
    
    records = query.order_by(Timekeeping.date.desc(), Timekeeping.time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'user_id': user_id,
        'records': [record.to_dict() for record in records.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': records.total,
            'pages': records.pages,
            'has_next': records.has_next,
            'has_prev': records.has_prev
        }
    }), 200

@timekeeping_bp.route('/department/<int:department_id>', methods=['GET'])
@jwt_required()
@require_permission('view_department_timekeeping')
@handle_errors
@paginate
def get_department_records(department_id, page=1, per_page=20):
    """Obtient les pointages d'un département"""
    from app.models.user import User
    
    date = request.args.get('date')
    if date:
        target_date = datetime.fromisoformat(date).date()
    else:
        target_date = datetime.utcnow().date()
    
    records = Timekeeping.query.join(User).filter(
        User.department_id == department_id,
        Timekeeping.date == target_date
    ).order_by(Timekeeping.time).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'department_id': department_id,
        'date': target_date.isoformat(),
        'records': [record.to_dict() for record in records.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': records.total,
            'pages': records.pages,
            'has_next': records.has_next,
            'has_prev': records.has_prev
        }
    }), 200

@timekeeping_bp.route('/<int:record_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_record(record_id):
    """Obtient un pointage spécifique"""
    record = Timekeeping.query.get_or_404(record_id)
    
    # Vérification des permissions
    current_user_id = get_jwt_identity()
    if record.user_id != current_user_id:
        # Vérifier si l'utilisateur a les permissions pour voir les autres
        user = User.query.get(current_user_id)
        if not user.can_view_reports():
            return jsonify({
                'error': 'Insufficient permissions',
                'message': 'Permissions insuffisantes'
            }), 403
    
    return jsonify({
        'record': record.to_dict()
    }), 200

@timekeeping_bp.route('/<int:record_id>', methods=['PUT'])
@jwt_required()
@require_permission('edit_timekeeping')
@handle_errors
def update_record(record_id):
    """Met à jour un pointage"""
    record = Timekeeping.query.get_or_404(record_id)
    data = request.get_json()
    
    # Mise à jour des champs autorisés
    allowed_fields = ['notes', 'location', 'device']
    for field in allowed_fields:
        if field in data:
            setattr(record, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Pointage mis à jour avec succès',
        'record': record.to_dict()
    }), 200

@timekeeping_bp.route('/<int:record_id>/validate', methods=['POST'])
@jwt_required()
@require_permission('validate_timekeeping')
@handle_errors
def validate_record(record_id):
    """Valide un pointage"""
    current_user_id = get_jwt_identity()
    record = Timekeeping.query.get_or_404(record_id)
    
    record.validate(current_user_id)
    db.session.commit()
    
    return jsonify({
        'message': 'Pointage validé avec succès',
        'record': record.to_dict()
    }), 200

@timekeeping_bp.route('/summary/<int:user_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_user_summary(user_id):
    """Obtient le résumé des pointages d'un utilisateur"""
    # Vérification des permissions
    current_user_id = get_jwt_identity()
    if user_id != current_user_id:
        user = User.query.get(current_user_id)
        if not user.can_view_reports():
            return jsonify({
                'error': 'Insufficient permissions',
                'message': 'Permissions insuffisantes'
            }), 403
    
    year = request.args.get('year', datetime.utcnow().year, type=int)
    month = request.args.get('month', datetime.utcnow().month, type=int)
    
    summary = Timekeeping.get_monthly_summary(user_id, year, month)
    
    return jsonify({
        'user_id': user_id,
        'summary': summary
    }), 200

@timekeeping_bp.route('/overtime', methods=['GET'])
@jwt_required()
@require_permission('view_overtime')
@handle_errors
def get_overtime_report():
    """Rapport des heures supplémentaires"""
    department_id = request.args.get('department_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.fromisoformat(end_date)
    else:
        end_date = datetime.utcnow()
    
    query = Timekeeping.query.filter(
        Timekeeping.overtime_hours > 0,
        Timekeeping.date >= start_date,
        Timekeeping.date <= end_date
    )
    
    if department_id:
        from app.models.user import User
        query = query.join(User).filter(User.department_id == department_id)
    
    records = query.order_by(Timekeeping.date.desc()).all()
    
    total_overtime = sum(r.overtime_hours for r in records)
    total_cost = sum(r.overtime_hours * r.user.hourly_rate for r in records)
    
    return jsonify({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'department_id': department_id,
        'total_overtime_hours': total_overtime,
        'total_cost': total_cost,
        'records': [record.to_dict() for record in records]
    }), 200

@timekeeping_bp.route('/late-report', methods=['GET'])
@jwt_required()
@require_permission('view_late_report')
@handle_errors
def get_late_report():
    """Rapport des retards"""
    department_id = request.args.get('department_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.fromisoformat(end_date)
    else:
        end_date = datetime.utcnow()
    
    query = Timekeeping.query.filter(
        Timekeeping.is_late == True,
        Timekeeping.date >= start_date,
        Timekeeping.date <= end_date
    )
    
    if department_id:
        from app.models.user import User
        query = query.join(User).filter(User.department_id == department_id)
    
    records = query.order_by(Timekeeping.date.desc()).all()
    
    total_late_minutes = sum(r.late_minutes for r in records)
    average_late_minutes = total_late_minutes / len(records) if records else 0
    
    return jsonify({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'department_id': department_id,
        'total_late_records': len(records),
        'total_late_minutes': total_late_minutes,
        'average_late_minutes': average_late_minutes,
        'records': [record.to_dict() for record in records]
    }), 200