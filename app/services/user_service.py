import bcrypt
from ..extensions import db
from ..models.user import User


def hash_pin(pin):
    return bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_pin(pin, pin_hash):
    return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))


def authenticate(username, pin):
    user = User.query.filter_by(username=username).first()
    if not user or not user.is_active_user:
        return None
    if verify_pin(pin, user.pin_hash):
        return user
    return None


def create_user(username, pin, role='user', color='#4A90D9'):
    if User.query.filter_by(username=username).first():
        return None, 'El nombre de usuario ya existe'
    user = User(
        username=username,
        pin_hash=hash_pin(pin),
        role=role,
        color=color,
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def change_pin(user, current_pin, new_pin):
    if not verify_pin(current_pin, user.pin_hash):
        return False, 'PIN actual incorrecto'
    if len(new_pin) != 4 or not new_pin.isdigit():
        return False, 'El PIN debe ser de 4 dígitos numéricos'
    user.pin_hash = hash_pin(new_pin)
    db.session.commit()
    return True, None


def reset_pin(user, new_pin):
    if len(new_pin) != 4 or not new_pin.isdigit():
        return False, 'El PIN debe ser de 4 dígitos numéricos'
    user.pin_hash = hash_pin(new_pin)
    db.session.commit()
    return True, None


def get_active_users():
    return User.query.filter_by(is_active_user=True).order_by(User.username).all()
