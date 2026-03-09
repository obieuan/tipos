from ..extensions import db
from datetime import datetime, timezone


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id])
    target_user = db.relationship('User', foreign_keys=[target_user_id])

    def to_dict(self, short=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'action': self.action,
            'reservation_id': self.reservation_id,
            'target_user_id': self.target_user_id,
            'target_name': self.target_user.name if self.target_user else None,
            'details': self.details,
            'created_at': self.created_at.isoformat(),
        }
        data['text'] = self._short_text() if short else self._full_text()
        return data

    def _time_str(self):
        if self.created_at:
            return self.created_at.strftime('%H:%M')
        return ''

    def _short_text(self):
        """Daily view: 'Juan reservó el espacio' (timestamp shown separately in UI)"""
        actor = self.user.name if self.user else 'Sistema'
        target = self.target_user.name if self.target_user else ''

        texts = {
            'reservation_created': f'{actor} reservó el espacio',
            'reservation_cancelled': f'{actor} canceló su reserva',
            'reservation_reassigned': f'{actor} reasignó la reserva a {target}',
            'guest_added': f'{actor} invitó a {target}',
            'guest_removed': f'{actor} removió a {target} como invitado',
            'guest_self_removed': f'{actor} se dio de baja como invitado',
            'day_blocked': f'{actor} bloqueó el día',
            'day_unblocked': f'{actor} desbloqueó el día',
            'user_created': f'{actor} creó al usuario {target}',
            'user_deactivated': f'{actor} desactivó a {target}',
            'settings_updated': f'{actor} actualizó la configuración',
        }
        return texts.get(self.action, f'{actor} realizó {self.action}')

    def _full_text(self):
        """Full format for general/monthly view: 'Juan reservó el 15 de marzo'"""
        actor = self.user.name if self.user else 'Sistema'
        target = self.target_user.name if self.target_user else ''
        details = self.details or {}
        date_str = details.get('date', '')

        texts = {
            'reservation_created': f'{actor} reservó el {date_str}',
            'reservation_cancelled': f'{actor} canceló su reserva del {date_str}',
            'reservation_reassigned': f'{actor} reasignó su reserva del {date_str} a {target}',
            'guest_added': f'{actor} agregó a {target} como invitado el {date_str}',
            'guest_removed': f'{actor} removió a {target} como invitado del {date_str}',
            'guest_self_removed': f'{actor} se removió como invitado del {date_str}',
            'day_blocked': f'{actor} bloqueó el día {date_str}',
            'day_unblocked': f'{actor} desbloqueó el día {date_str}',
            'user_created': f'{actor} creó al usuario {target}',
            'user_deactivated': f'{actor} desactivó al usuario {target}',
            'settings_updated': f'{actor} actualizó la configuración',
        }
        return texts.get(self.action, f'{actor} realizó {self.action}')
