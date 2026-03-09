from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import user  # noqa: F401 - register models

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return db.session.get(User, int(user_id))

    from .api.auth import auth_bp
    from .api.reservations import reservations_bp
    from .api.calendar import calendar_bp
    from .api.history import history_bp
    from .api.admin import admin_bp
    from .views import views_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(reservations_bp, url_prefix='/api/reservations')
    app.register_blueprint(calendar_bp, url_prefix='/api/calendar')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(views_bp)

    return app
