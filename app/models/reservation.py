from ..extensions import db
from datetime import datetime, timezone


class Reservation(db.Model):
    __tablename__ = 'reservations'
    __table_args__ = (
        db.UniqueConstraint('date', 'block', name='uq_reservation_date_block'),
    )

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    block = db.Column(db.String(20), default='full_day')
    disclaimer_accepted = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    guests = db.relationship('ReservationGuest', backref='reservation',
                             lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_guests=False):
        data = {
            'id': self.id,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name,
            'owner_color': self.owner.color,
            'date': self.date.isoformat(),
            'block': self.block,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
        }
        if include_guests:
            data['guests'] = [g.guest.to_dict() for g in self.guests.all()]
        return data
