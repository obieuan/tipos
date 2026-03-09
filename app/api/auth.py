import time
from collections import defaultdict
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db
from ..services.user_service import authenticate, change_pin

auth_bp = Blueprint('auth', __name__)

# Simple in-memory rate limiter for failed login attempts only
_failed_attempts = defaultdict(list)
MAX_FAILED = 5
WINDOW_SECONDS = 900  # 15 minutes


def _check_rate_limit(ip):
    now = time.time()
    # Clean old attempts
    _failed_attempts[ip] = [t for t in _failed_attempts[ip] if now - t < WINDOW_SECONDS]
    return len(_failed_attempts[ip]) >= MAX_FAILED


def _record_failed(ip):
    _failed_attempts[ip].append(time.time())


@auth_bp.route('/login', methods=['POST'])
def login():
    ip = request.remote_addr
    if _check_rate_limit(ip):
        return jsonify({'error': 'Demasiados intentos. Espera unos minutos.'}), 429

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    username = data.get('username', '').strip()
    pin = data.get('pin', '')

    if not username or not pin:
        return jsonify({'error': 'Usuario y PIN son requeridos'}), 400

    user = authenticate(username, pin)
    if not user:
        _record_failed(ip)
        return jsonify({'error': 'Usuario o PIN incorrecto'}), 401

    # Successful login clears failed attempts
    _failed_attempts.pop(ip, None)
    login_user(user, remember=True)
    return jsonify({'user': user.to_dict()})


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Sesión cerrada'})


@auth_bp.route('/change-pin', methods=['POST'])
@login_required
def change_pin_route():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    current_pin = data.get('current_pin', '')
    new_pin = data.get('new_pin', '')

    if not current_pin or not new_pin:
        return jsonify({'error': 'PIN actual y nuevo son requeridos'}), 400

    success, error = change_pin(current_user, current_pin, new_pin)
    if not success:
        return jsonify({'error': error}), 400

    return jsonify({'message': 'PIN actualizado correctamente'})


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': current_user.to_dict()})


@auth_bp.route('/update-profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos inválidos'}), 400

    display_name = data.get('display_name', '').strip()
    if not display_name:
        return jsonify({'error': 'El nombre para mostrar es requerido'}), 400
    if len(display_name) > 100:
        return jsonify({'error': 'El nombre es demasiado largo'}), 400

    current_user.display_name = display_name
    db.session.commit()
    return jsonify({'user': current_user.to_dict()})
