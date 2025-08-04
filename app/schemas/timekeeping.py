from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

class TimekeepingCreateSchema(Schema):
    """Schéma de validation pour la création d'un pointage"""
    type = fields.Str(required=True, validate=validate.OneOf(['arrival', 'departure', 'break_start', 'break_end']), error_messages={
        'required': 'Le type de pointage est requis',
        'validator_failed': 'Type de pointage invalide. Types autorisés: arrival, departure, break_start, break_end'
    })
    location = fields.Str(validate=validate.Length(max=100), error_messages={
        'validator_failed': 'La localisation ne peut pas dépasser 100 caractères'
    })
    device = fields.Str(validate=validate.Length(max=50), error_messages={
        'validator_failed': 'L\'appareil ne peut pas dépasser 50 caractères'
    })
    notes = fields.Str(validate=validate.Length(max=500), error_messages={
        'validator_failed': 'Les notes ne peuvent pas dépasser 500 caractères'
    })

class TimekeepingUpdateSchema(Schema):
    """Schéma de validation pour la mise à jour d'un pointage"""
    location = fields.Str(validate=validate.Length(max=100), error_messages={
        'validator_failed': 'La localisation ne peut pas dépasser 100 caractères'
    })
    device = fields.Str(validate=validate.Length(max=50), error_messages={
        'validator_failed': 'L\'appareil ne peut pas dépasser 50 caractères'
    })
    notes = fields.Str(validate=validate.Length(max=500), error_messages={
        'validator_failed': 'Les notes ne peuvent pas dépasser 500 caractères'
    })

class TimekeepingSchema(Schema):
    """Schéma de sérialisation pour les pointages"""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    date = fields.Date(required=True)
    type = fields.Str(required=True)
    time = fields.DateTime(required=True)
    expected_time = fields.DateTime(allow_none=True)
    is_late = fields.Bool(dump_only=True)
    late_minutes = fields.Int(dump_only=True)
    overtime_hours = fields.Float(dump_only=True)
    location = fields.Str(allow_none=True)
    device = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    is_validated = fields.Bool(dump_only=True)
    validated_by_id = fields.Int(allow_none=True)
    validated_at = fields.DateTime(allow_none=True)
    is_weekend = fields.Bool(dump_only=True)
    is_holiday = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Relations
    user = fields.Nested('UserSchema', dump_only=True)
    validated_by = fields.Nested('UserSchema', dump_only=True)

class TimekeepingSummarySchema(Schema):
    """Schéma pour le résumé des pointages"""
    date = fields.Date(required=True)
    arrival = fields.Nested(TimekeepingSchema, allow_none=True)
    departure = fields.Nested(TimekeepingSchema, allow_none=True)
    total_hours = fields.Float(required=True)
    overtime_hours = fields.Float(required=True)
    late_minutes = fields.Int(required=True)

class TimekeepingMonthlySummarySchema(Schema):
    """Schéma pour le résumé mensuel des pointages"""
    year = fields.Int(required=True)
    month = fields.Int(required=True)
    working_days = fields.Int(required=True)
    total_overtime_hours = fields.Float(required=True)
    total_late_minutes = fields.Int(required=True)
    average_late_minutes = fields.Float(required=True)

class TimekeepingStatisticsSchema(Schema):
    """Schéma pour les statistiques de pointage"""
    user_id = fields.Int(required=True)
    period = fields.Dict(required=True)
    statistics = fields.Dict(required=True)