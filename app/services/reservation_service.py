from datetime import date, timedelta
from ..extensions import db
from ..models.reservation import Reservation
from ..models.blocked_day import BlockedDay
from ..models.reservation_guest import ReservationGuest
from ..models.app_setting import AppSetting
from .log_service import log_action


def _get_int_setting(key, default):
    val = AppSetting.get(key, str(default))
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def validate_reservation_date(reservation_date, exclude_reservation_id=None):
    today = date.today()

    if reservation_date < today:
        return 'No se puede reservar una fecha pasada'

    min_days = _get_int_setting('min_days_ahead', 0)
    max_days = _get_int_setting('max_days_ahead', 365)

    diff = (reservation_date - today).days
    if diff < min_days:
        return f'Debes reservar con al menos {min_days} días de anticipación'
    if diff > max_days:
        return f'No puedes reservar con más de {max_days} días de anticipación'

    blocked = BlockedDay.query.filter_by(date=reservation_date).first()
    if blocked:
        return 'Este día está bloqueado'

    existing = Reservation.query.filter_by(date=reservation_date, block='full_day')
    if exclude_reservation_id:
        existing = existing.filter(Reservation.id != exclude_reservation_id)
    if existing.first():
        return 'Ya existe una reserva para este día'

    return None


def create_reservation(user, reservation_date, notes=None):
    error = validate_reservation_date(reservation_date)
    if error:
        return None, error

    reservation = Reservation(
        owner_id=user.id,
        date=reservation_date,
        block='full_day',
        disclaimer_accepted=True,
        notes=notes,
    )
    db.session.add(reservation)
    db.session.commit()

    log_action(user.id, 'reservation_created', reservation_id=reservation.id,
               details={'date': reservation_date.isoformat()})

    return reservation, None


def cancel_reservation(user, reservation):
    if reservation.owner_id != user.id and not user.is_admin:
        return False, 'Solo el dueño puede cancelar esta reserva'
    if reservation.date < date.today():
        return False, 'No se puede cancelar una reserva pasada'

    date_str = reservation.date.isoformat()
    res_id = reservation.id
    db.session.delete(reservation)
    db.session.commit()

    log_action(user.id, 'reservation_cancelled', reservation_id=res_id,
               details={'date': date_str})
    return True, None


def reassign_reservation(user, reservation, new_owner):
    if reservation.owner_id != user.id and not user.is_admin:
        return False, 'Solo el dueño puede reasignar esta reserva'
    if reservation.date < date.today():
        return False, 'No se puede reasignar una reserva pasada'

    old_owner_id = reservation.owner_id
    reservation.owner_id = new_owner.id
    db.session.commit()

    log_action(user.id, 'reservation_reassigned', reservation_id=reservation.id,
               target_user_id=new_owner.id,
               details={'date': reservation.date.isoformat(), 'old_owner_id': old_owner_id})
    return True, None


def add_guest(user, reservation, guest_user):
    if reservation.owner_id != user.id and not user.is_admin:
        return False, 'Solo el dueño puede agregar invitados'
    if guest_user.id == reservation.owner_id:
        return False, 'El dueño no puede ser invitado de su propia reserva'

    existing = ReservationGuest.query.filter_by(
        reservation_id=reservation.id, guest_user_id=guest_user.id
    ).first()
    if existing:
        return False, 'Este usuario ya es invitado'

    guest_entry = ReservationGuest(
        reservation_id=reservation.id,
        guest_user_id=guest_user.id,
    )
    db.session.add(guest_entry)
    db.session.commit()

    log_action(user.id, 'guest_added', reservation_id=reservation.id,
               target_user_id=guest_user.id,
               details={'date': reservation.date.isoformat()})
    return True, None


def remove_guest(user, reservation, guest_user):
    guest_entry = ReservationGuest.query.filter_by(
        reservation_id=reservation.id, guest_user_id=guest_user.id
    ).first()
    if not guest_entry:
        return False, 'Este usuario no es invitado'

    is_self = user.id == guest_user.id
    is_owner = user.id == reservation.owner_id

    if not is_self and not is_owner and not user.is_admin:
        return False, 'No tienes permiso para quitar este invitado'

    db.session.delete(guest_entry)
    db.session.commit()

    action = 'guest_self_removed' if is_self else 'guest_removed'
    log_action(user.id, action, reservation_id=reservation.id,
               target_user_id=guest_user.id,
               details={'date': reservation.date.isoformat()})
    return True, None


def get_month_reservations(year, month):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return Reservation.query.filter(
        Reservation.date >= start, Reservation.date < end
    ).all()
