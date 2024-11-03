# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin

bp = Blueprint('auth', __name__)

# Простой класс пользователя для демонстрации
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# Глобальный объект для хранения пользователя
admin_user = User(1)

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'timetable.index'  # Редирект на главную при необходимости входа

    @login_manager.user_loader
    def load_user(user_id):
        if int(user_id) == 1:
            return admin_user
        return None

@bp.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == current_app.config['ADMIN_PASSWORD']:
        login_user(admin_user)
        session['is_admin'] = True
        flash('Вы успешно вошли как администратор', 'success')
    else:
        flash('Неверный пароль', 'error')
    return redirect(url_for('timetable.index'))

@bp.route('/logout')
def logout():
    logout_user()
    session.pop('is_admin', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('timetable.index'))