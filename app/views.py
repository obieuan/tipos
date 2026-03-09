from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from .models.app_setting import AppSetting

views_bp = Blueprint('views', __name__)


@views_bp.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('views.calendar_page'))
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    return render_template('login.html', site_name=site_name)


@views_bp.route('/')
@login_required
def calendar_page():
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    disclaimer = AppSetting.get('disclaimer_text',
                                'Al reservar, acepto respetar las reglas del espacio y dejarlo en condiciones adecuadas.')
    return render_template('calendar.html', site_name=site_name, disclaimer=disclaimer)


@views_bp.route('/historial')
@login_required
def history_page():
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    return render_template('history.html', site_name=site_name)


@views_bp.route('/perfil')
@login_required
def profile_page():
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    return render_template('profile.html', site_name=site_name)


@views_bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('views.calendar_page'))
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    return render_template('admin/dashboard.html', site_name=site_name)


@views_bp.route('/admin/usuarios')
@login_required
def admin_users():
    if not current_user.is_admin:
        return redirect(url_for('views.calendar_page'))
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    return render_template('admin/users.html', site_name=site_name)


@views_bp.route('/admin/configuracion')
@login_required
def admin_settings():
    if not current_user.is_admin:
        return redirect(url_for('views.calendar_page'))
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    return render_template('admin/settings.html', site_name=site_name)


@views_bp.route('/admin/bloquear')
@login_required
def admin_blocked_days():
    if not current_user.is_admin:
        return redirect(url_for('views.calendar_page'))
    site_name = AppSetting.get('site_name', 'Tipos Beach House')
    return render_template('admin/blocked_days.html', site_name=site_name)
