from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models.reservation import Reservation
from ..models.user import User
from ..services import reservation_service

reservations_bp = Blueprint('reservations', __name__)


@reservations_bp.route('', methods=['GET'])
@login_required
def get_reservations():
    month_str = request.args.get('month')
    if not month_str:
        return jsonify({'error': 'Parámetro month requerido (YYYY-MM)'}), 400
    try:
        parts = month_str.split('-')
        year, month = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return jsonify({'error': 'Formato de mes inválido (YYYY-MM)'}), 400

    reservations = reservation_service.get_month_reservations(year, month)
    return jsonify([r.to_dict(include_guests=True) for r in reservations])


@reservations_bp.route('', methods=['POST'])
@login_required
def create_reservation():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    date_str = data.get('date')
    notes = data.get('notes', '').strip() or None

    if not date_str:
        return jsonify({'error': 'Fecha requerida'}), 400

    try:
        reservation_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido (YYYY-MM-DD)'}), 400

    reservation, error = reservation_service.create_reservation(
        current_user, reservation_date, notes
    )
    if error:
        return jsonify({'error': error}), 400

    return jsonify(reservation.to_dict(include_guests=True)), 201


@reservations_bp.route('/<int:reservation_id>', methods=['DELETE'])
@login_required
def delete_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    success, error = reservation_service.cancel_reservation(current_user, reservation)
    if not success:
        return jsonify({'error': error}), 400

    return jsonify({'message': 'Reserva cancelada'})


@reservations_bp.route('/<int:reservation_id>/reassign', methods=['PUT'])
@login_required
def reassign_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    data = request.get_json()
    new_owner_id = data.get('new_owner_id') if data else None
    if not new_owner_id:
        return jsonify({'error': 'new_owner_id requerido'}), 400

    new_owner = db.session.get(User, new_owner_id)
    if not new_owner or not new_owner.is_active_user:
        return jsonify({'error': 'Usuario no encontrado o inactivo'}), 404

    success, error = reservation_service.reassign_reservation(
        current_user, reservation, new_owner
    )
    if not success:
        return jsonify({'error': error}), 400

    return jsonify(reservation.to_dict(include_guests=True))


@reservations_bp.route('/<int:reservation_id>/guests', methods=['POST'])
@login_required
def add_guest(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    data = request.get_json()
    user_id = data.get('user_id') if data else None
    if not user_id:
        return jsonify({'error': 'user_id requerido'}), 400

    guest_user = db.session.get(User, user_id)
    if not guest_user or not guest_user.is_active_user:
        return jsonify({'error': 'Usuario no encontrado o inactivo'}), 404

    success, error = reservation_service.add_guest(current_user, reservation, guest_user)
    if not success:
        return jsonify({'error': error}), 400

    return jsonify(reservation.to_dict(include_guests=True))


@reservations_bp.route('/<int:reservation_id>/guests/me', methods=['DELETE'])
@login_required
def remove_self_as_guest(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    success, error = reservation_service.remove_guest(
        current_user, reservation, current_user
    )
    if not success:
        return jsonify({'error': error}), 400

    return jsonify({'message': 'Te has removido como invitado'})


@reservations_bp.route('/<int:reservation_id>/guests/<int:user_id>', methods=['DELETE'])
@login_required
def remove_guest(reservation_id, user_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Reserva no encontrada'}), 404

    guest_user = db.session.get(User, user_id)
    if not guest_user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    success, error = reservation_service.remove_guest(
        current_user, reservation, guest_user
    )
    if not success:
        return jsonify({'error': error}), 400

    return jsonify(reservation.to_dict(include_guests=True))
