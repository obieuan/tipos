from flask_login import UserMixin
from ..extensions import db
from datetime import datetime, timezone


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    pin_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active_user = db.Column('is_active', db.Boolean, default=True)
    color = db.Column(db.String(7), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reservations = db.relationship('Reservation', backref='owner', lazy='dynamic',
                                   foreign_keys='Reservation.owner_id')

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_active(self):
        return self.is_active_user

    @property
    def name(self):
        """Display name, falls back to username."""
        return self.display_name or self.username

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active_user,
            'color': self.color,
            'created_at': self.created_at.isoformat(),
        }
