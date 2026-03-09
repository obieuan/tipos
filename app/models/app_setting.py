from ..extensions import db
from datetime import datetime, timezone


class AppSetting(db.Model):
    __tablename__ = 'app_settings'

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    @staticmethod
    def get(key, default=None):
        setting = db.session.get(AppSetting, key)
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        setting = db.session.get(AppSetting, key)
        if setting:
            setting.value = str(value)
        else:
            setting = AppSetting(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()
        return setting

    @staticmethod
    def get_all():
        settings = AppSetting.query.all()
        return {s.key: s.value for s in settings}
