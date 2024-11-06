from functools import wraps
from flask import session, redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not session.get('is_admin'):
            flash('Доступ запрещен. Необходимы права администратора.', 'error')
            return redirect(url_for('timetable.index'))
        return f(*args, **kwargs)
    return decorated_function