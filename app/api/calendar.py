from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required
from ..models.blocked_day import BlockedDay
from ..services.reservation_service import get_month_reservations

calendar_bp = Blueprint('calendar', __name__)


@calendar_bp.route('', methods=['GET'])
@login_required
def get_calendar():
    month_str = request.args.get('month')
    if not month_str:
        return jsonify({'error': 'Parámetro month requerido (YYYY-MM)'}), 400
    try:
        parts = month_str.split('-')
        year, month = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return jsonify({'error': 'Formato de mes inválido (YYYY-MM)'}), 400

    reservations = get_month_reservations(year, month)

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    blocked = BlockedDay.query.filter(
        BlockedDay.date >= start, BlockedDay.date < end
    ).all()

    return jsonify({
        'reservations': [r.to_dict(include_guests=True) for r in reservations],
        'blocked_days': [b.to_dict() for b in blocked],
    })


@calendar_bp.route('/blocked-days', methods=['GET'])
@login_required
def get_blocked_days():
    month_str = request.args.get('month')
    if not month_str:
        return jsonify({'error': 'Parámetro month requerido (YYYY-MM)'}), 400
    try:
        parts = month_str.split('-')
        year, month = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return jsonify({'error': 'Formato de mes inválido (YYYY-MM)'}), 400

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    blocked = BlockedDay.query.filter(
        BlockedDay.date >= start, BlockedDay.date < end
    ).all()

    return jsonify([b.to_dict() for b in blocked])
