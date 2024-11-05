# routes/notifications.py

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import uuid
from models.notifications import NotificationManager, Notification
from functools import wraps
from config.config import Config
import os


bp = Blueprint('notifications', __name__, url_prefix='/secret-notifications')

notification_manager = NotificationManager(os.path.join(Config.DATA_DIR, 'notifications.json'))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret_key = request.args.get('key')
        if secret_key != Config.NOTIFICATION_SECRET_KEY:
            return "Доступ запрещен", 403
        return f(*args, **kwargs)

    return decorated_function


@bp.route('/')
@admin_required
def index():
    """Страница управления уведомлениями"""
    notifications = notification_manager.get_notifications()
    return render_template('notifications/admin.html', notifications=notifications)


@bp.route('/create', methods=['POST'])
@admin_required
def create():
    """Создание нового уведомления"""
    try:
        data = request.form

        # Парсим даты
        active_from = datetime.strptime(data['active_from'], '%Y-%m-%dT%H:%M')
        active_until = datetime.strptime(data['active_until'], '%Y-%m-%dT%H:%M')

        # Создаем уведомление
        notification = Notification(
            id=str(uuid.uuid4()),
            title=data['title'],
            message=data['message'],
            type=data['type'],
            active_from=active_from,
            active_until=active_until,
            priority=data['priority']
        )

        # Обрабатываем features
        features = data.get('features', '').split('\n')
        notification.features = [f.strip() for f in features if f.strip()]

        # Сохраняем
        notification_manager.save_notification(notification)

        return redirect(url_for('notifications.index', key=request.args.get('key')))

    except Exception as e:
        return str(e), 400


@bp.route('/delete/<notification_id>', methods=['POST'])
@admin_required
def delete(notification_id):
    """Удаление уведомления"""
    notification_manager.delete_notification(notification_id)
    return redirect(url_for('notifications.index', key=request.args.get('key')))


# API для фронтенда
@bp.route('/api/active')
def get_active():
    """Получение активных уведомлений"""
    notifications = notification_manager.get_notifications()
    now = datetime.now()

    # Фильтруем активные уведомления
    active_notifications = [
        n for n in notifications
        if datetime.fromisoformat(n['active_from']) <= now <= datetime.fromisoformat(n['active_until'])
    ]

    return jsonify(active_notifications)