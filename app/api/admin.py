from datetime import date
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models.user import User
from ..models.blocked_day import BlockedDay
from ..models.reservation import Reservation
from ..models.app_setting import AppSetting
from ..services.user_service import create_user, reset_pin, hash_pin
from ..services.log_service import log_action

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated


# --- Users ---

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user_route():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    username = data.get('username', '').strip()
    pin = data.get('pin', '')
    role = data.get('role', 'user')
    color = data.get('color', '#4A90D9')

    if not username or not pin:
        return jsonify({'error': 'Usuario y PIN son requeridos'}), 400
    if len(pin) != 4 or not pin.isdigit():
        return jsonify({'error': 'El PIN debe ser de 4 dígitos numéricos'}), 400
    if role not in ('user', 'admin'):
        return jsonify({'error': 'Rol inválido'}), 400

    user, error = create_user(username, pin, role, color)
    if error:
        return jsonify({'error': error}), 400

    log_action(current_user.id, 'user_created', target_user_id=user.id)
    return jsonify(user.to_dict()), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    if 'username' in data:
        new_username = data['username'].strip()
        existing = User.query.filter(User.username == new_username, User.id != user_id).first()
        if existing:
            return jsonify({'error': 'El nombre de usuario ya existe'}), 400
        user.username = new_username
    if 'role' in data and data['role'] in ('user', 'admin'):
        user.role = data['role']
    if 'color' in data:
        user.color = data['color']

    db.session.commit()
    return jsonify(user.to_dict())


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['PUT'])
@admin_required
def deactivate_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    if user.id == current_user.id:
        return jsonify({'error': 'No puedes desactivarte a ti mismo'}), 400

    user.is_active_user = False
    db.session.commit()

    log_action(current_user.id, 'user_deactivated', target_user_id=user.id)
    return jsonify(user.to_dict())


@admin_bp.route('/users/<int:user_id>/activate', methods=['PUT'])
@admin_required
def activate_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    user.is_active_user = True
    db.session.commit()
    return jsonify(user.to_dict())


@admin_bp.route('/users/<int:user_id>/reset-pin', methods=['PUT'])
@admin_required
def reset_pin_route(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    data = request.get_json()
    new_pin = data.get('new_pin', '') if data else ''

    success, error = reset_pin(user, new_pin)
    if not success:
        return jsonify({'error': error}), 400

    return jsonify({'message': 'PIN reseteado correctamente'})


# --- Settings ---

@admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings():
    return jsonify(AppSetting.get_all())


@admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    allowed_keys = {'disclaimer_text', 'booking_mode', 'min_days_ahead',
                    'max_days_ahead', 'site_name', 'disclaimer_url'}
    for key, value in data.items():
        if key in allowed_keys:
            AppSetting.set(key, value)

    log_action(current_user.id, 'settings_updated')
    return jsonify(AppSetting.get_all())


# --- Blocked Days ---

@admin_bp.route('/blocked-days', methods=['POST'])
@admin_required
def block_day():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    date_str = data.get('date')
    reason = data.get('reason', '').strip() or None

    if not date_str:
        return jsonify({'error': 'Fecha requerida'}), 400

    try:
        block_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400

    existing = BlockedDay.query.filter_by(date=block_date).first()
    if existing:
        return jsonify({'error': 'Este día ya está bloqueado'}), 400

    # Check for existing reservation
    reservation = Reservation.query.filter_by(date=block_date, block='full_day').first()
    if reservation and data.get('cancel_reservation'):
        date_iso = reservation.date.isoformat()
        res_id = reservation.id
        db.session.delete(reservation)
        log_action(current_user.id, 'reservation_cancelled', reservation_id=res_id,
                   details={'date': date_iso, 'reason': 'Día bloqueado por admin'})

    blocked = BlockedDay(
        date=block_date,
        reason=reason,
        blocked_by=current_user.id,
    )
    db.session.add(blocked)
    db.session.commit()

    log_action(current_user.id, 'day_blocked',
               details={'date': block_date.isoformat(), 'reason': reason})

    has_reservation = reservation is not None and not data.get('cancel_reservation')
    result = blocked.to_dict()
    if has_reservation:
        result['warning'] = 'Existe una reserva en este día'
        result['reservation'] = reservation.to_dict()

    return jsonify(result), 201


@admin_bp.route('/blocked-days/<int:blocked_id>', methods=['DELETE'])
@admin_required
def unblock_day(blocked_id):
    blocked = db.session.get(BlockedDay, blocked_id)
    if not blocked:
        return jsonify({'error': 'Día bloqueado no encontrado'}), 404

    date_str = blocked.date.isoformat()
    db.session.delete(blocked)
    db.session.commit()

    log_action(current_user.id, 'day_unblocked', details={'date': date_str})
    return jsonify({'message': 'Día desbloqueado'})
