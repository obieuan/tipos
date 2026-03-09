from ..extensions import db
from datetime import datetime, timezone


class ReservationGuest(db.Model):
    __tablename__ = 'reservation_guests'
    __table_args__ = (
        db.UniqueConstraint('reservation_id', 'guest_user_id',
                            name='uq_reservation_guest'),
    )

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id',
                               ondelete='CASCADE'), nullable=False)
    guest_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    guest = db.relationship('User', foreign_keys=[guest_user_id])
