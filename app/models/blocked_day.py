from ..extensions import db
from datetime import datetime, timezone


class BlockedDay(db.Model):
    __tablename__ = 'blocked_days'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    reason = db.Column(db.String(255))
    blocked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    blocker = db.relationship('User', foreign_keys=[blocked_by])

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'reason': self.reason,
            'blocked_by': self.blocked_by,
            'created_at': self.created_at.isoformat(),
        }
