"""Seed script: creates admin user and default app settings."""

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.app_setting import AppSetting
from app.services.user_service import hash_pin


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Default settings
        defaults = {
            'disclaimer_text': 'Al reservar, acepto respetar las reglas del espacio y dejarlo en condiciones adecuadas.',
            'booking_mode': 'full_day',
            'min_days_ahead': '0',
            'max_days_ahead': '365',
            'site_name': 'Tipos Beach House',
        }
        for key, value in defaults.items():
            if not db.session.get(AppSetting, key):
                db.session.add(AppSetting(key=key, value=value))

        # Admin user
        if not User.query.filter_by(username='Admin').first():
            admin = User(
                username='Admin',
                pin_hash=hash_pin('1234'),
                role='admin',
                color='#333333',
            )
            db.session.add(admin)
            print('Admin user created (username: Admin, PIN: 1234)')

        # Test users
        test_users = [
            ('Juan', '1111', '#4A90D9'),
            ('María', '2222', '#E07B4C'),
            ('Carlos', '3333', '#7BC47F'),
        ]
        for username, pin, color in test_users:
            if not User.query.filter_by(username=username).first():
                db.session.add(User(
                    username=username,
                    pin_hash=hash_pin(pin),
                    role='user',
                    color=color,
                ))
                print(f'Test user created: {username} (PIN: {pin})')

        db.session.commit()
        print('Seed complete.')


if __name__ == '__main__':
    seed()
