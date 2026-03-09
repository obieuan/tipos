from datetime import date, datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models.activity_log import ActivityLog

history_bp = Blueprint('history', __name__)


@history_bp.route('', methods=['GET'])
@login_required
def get_history():
    query = ActivityLog.query

    date_str = request.args.get('date')
    month_str = request.args.get('month')
    short_format = False

    if date_str:
        # Daily view: events related to this specific date (by reservation date in details)
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido (YYYY-MM-DD)'}), 400
        query = query.filter(
            db.func.json_extract(ActivityLog.details, '$.date') == date_str
        )
        short_format = True
    elif month_str:
        # Monthly/general view: events created during this month
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
        query = query.filter(
            ActivityLog.created_at >= datetime(start.year, start.month, start.day),
            ActivityLog.created_at < datetime(end.year, end.month, end.day),
        )

    # Admin filters
    if current_user.is_admin:
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        if user_id:
            query = query.filter(ActivityLog.user_id == int(user_id))
        if action:
            query = query.filter(ActivityLog.action == action)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'items': [entry.to_dict(short=short_format) for entry in pagination.items],
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
    })
