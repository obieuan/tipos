from ..extensions import db
from ..models.activity_log import ActivityLog


def log_action(user_id, action, reservation_id=None, target_user_id=None, details=None):
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        reservation_id=reservation_id,
        target_user_id=target_user_id,
        details=details,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
