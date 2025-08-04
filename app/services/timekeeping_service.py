from datetime import datetime, time, timedelta
from app import db
from app.models.timekeeping import Timekeeping
from app.models.user import User

class TimekeepingService:
    """Service pour la gestion des pointages"""
    
    @staticmethod
    def create_punch(user_id, punch_type, location=None, device=None, notes=None):
        """Crée un nouveau pointage"""
        now = datetime.utcnow()
        
        # Vérification de l'utilisateur
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Utilisateur non trouvé')
        
        # Vérification du type de pointage
        valid_types = ['arrival', 'departure', 'break_start', 'break_end']
        if punch_type not in valid_types:
            raise ValueError(f'Type de pointage invalide. Types autorisés: {valid_types}')
        
        # Vérification de la cohérence des pointages
        today_records = Timekeeping.query.filter_by(
            user_id=user_id,
            date=now.date()
        ).all()
        
        # Vérification des règles métier
        if punch_type == 'arrival':
            # Vérifier s'il n'y a pas déjà un pointage d'arrivée aujourd'hui
            existing_arrival = next((r for r in today_records if r.type == 'arrival'), None)
            if existing_arrival:
                raise ValueError('Pointage d\'arrivée déjà effectué aujourd\'hui')
        
        elif punch_type == 'departure':
            # Vérifier qu'il y a un pointage d'arrivée
            arrival = next((r for r in today_records if r.type == 'arrival'), None)
            if not arrival:
                raise ValueError('Pointage d\'arrivée requis avant le pointage de départ')
            
            # Vérifier qu'il n'y a pas déjà un pointage de départ
            existing_departure = next((r for r in today_records if r.type == 'departure'), None)
            if existing_departure:
                raise ValueError('Pointage de départ déjà effectué aujourd\'hui')
        
        # Calcul de l'heure attendue
        expected_time = TimekeepingService.get_expected_time(punch_type, now)
        
        # Calcul des retards et heures supplémentaires
        is_late = False
        late_minutes = 0
        overtime_hours = 0.0
        
        if expected_time:
            if now.time() > expected_time:
                is_late = True
                late_minutes = int((now - datetime.combine(now.date(), expected_time)).total_seconds() / 60)
        
        # Calcul des heures supplémentaires (pour le pointage de départ)
        if punch_type == 'departure':
            overtime_hours = TimekeepingService.calculate_overtime_hours(now)
        
        # Création du pointage
        timekeeping = Timekeeping(
            user_id=user_id,
            date=now.date(),
            type=punch_type,
            time=now,
            expected_time=datetime.combine(now.date(), expected_time) if expected_time else None,
            is_late=is_late,
            late_minutes=late_minutes,
            overtime_hours=overtime_hours,
            location=location,
            device=device,
            notes=notes
        )
        
        db.session.add(timekeeping)
        db.session.commit()
        
        return timekeeping
    
    @staticmethod
    def get_expected_time(punch_type, current_time):
        """Obtient l'heure attendue selon le type de pointage"""
        # Horaires par défaut (à personnaliser selon les besoins)
        schedules = {
            'arrival': time(9, 0),    # 9h00
            'departure': time(17, 30), # 17h30
            'break_start': time(12, 0), # 12h00
            'break_end': time(13, 0)   # 13h00
        }
        
        return schedules.get(punch_type)
    
    @staticmethod
    def calculate_overtime_hours(current_time):
        """Calcule les heures supplémentaires"""
        normal_end_time = time(17, 30)  # 17h30
        
        if current_time.time() > normal_end_time:
            overtime_minutes = (current_time - datetime.combine(current_time.date(), normal_end_time)).total_seconds() / 60
            return round(overtime_minutes / 60, 2)
        
        return 0.0
    
    @staticmethod
    def get_user_statistics(user_id, start_date=None, end_date=None):
        """Obtient les statistiques d'un utilisateur"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        records = Timekeeping.query.filter(
            Timekeeping.user_id == user_id,
            Timekeeping.date >= start_date.date(),
            Timekeeping.date <= end_date.date()
        ).all()
        
        # Calculs
        total_work_days = len(set(r.date for r in records if r.type == 'arrival'))
        total_overtime_hours = sum(r.overtime_hours for r in records)
        total_late_minutes = sum(r.late_minutes for r in records)
        late_days = len([r for r in records if r.is_late])
        
        # Taux de présence
        working_days = 22  # Jours ouvrables par mois
        attendance_rate = (total_work_days / working_days) * 100 if working_days > 0 else 0
        
        # Taux de ponctualité
        punctuality_rate = ((total_work_days - late_days) / total_work_days) * 100 if total_work_days > 0 else 100
        
        return {
            'user_id': user_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'statistics': {
                'total_work_days': total_work_days,
                'total_overtime_hours': total_overtime_hours,
                'total_late_minutes': total_late_minutes,
                'late_days': late_days,
                'attendance_rate': round(attendance_rate, 2),
                'punctuality_rate': round(punctuality_rate, 2)
            }
        }
    
    @staticmethod
    def get_department_statistics(department_id, start_date=None, end_date=None):
        """Obtient les statistiques d'un département"""
        from app.models.user import User
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        records = Timekeeping.query.join(User).filter(
            User.department_id == department_id,
            Timekeeping.date >= start_date.date(),
            Timekeeping.date <= end_date.date()
        ).all()
        
        # Calculs par utilisateur
        user_stats = {}
        for record in records:
            if record.user_id not in user_stats:
                user_stats[record.user_id] = {
                    'user': record.user.to_public_dict(),
                    'work_days': 0,
                    'overtime_hours': 0,
                    'late_minutes': 0,
                    'late_days': 0
                }
            
            user_stats[record.user_id]['work_days'] = len(set(
                r.date for r in records if r.user_id == record.user_id and r.type == 'arrival'
            ))
            user_stats[record.user_id]['overtime_hours'] += record.overtime_hours
            user_stats[record.user_id]['late_minutes'] += record.late_minutes
            if record.is_late:
                user_stats[record.user_id]['late_days'] += 1
        
        # Statistiques globales du département
        total_work_days = sum(stats['work_days'] for stats in user_stats.values())
        total_overtime_hours = sum(stats['overtime_hours'] for stats in user_stats.values())
        total_late_minutes = sum(stats['late_minutes'] for stats in user_stats.values())
        
        return {
            'department_id': department_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'statistics': {
                'total_work_days': total_work_days,
                'total_overtime_hours': total_overtime_hours,
                'total_late_minutes': total_late_minutes,
                'average_overtime_per_user': total_overtime_hours / len(user_stats) if user_stats else 0,
                'average_late_minutes_per_user': total_late_minutes / len(user_stats) if user_stats else 0
            },
            'user_statistics': list(user_stats.values())
        }