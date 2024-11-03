# utils/telegram_notifier.py
from flask import request, current_app
from functools import wraps
from datetime import datetime
import requests


def get_client_ip():
    """Получение IP-адреса клиента"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr


def send_notification(message):
    """
    Простая функция для отправки уведомлений в Telegram
    """
    try:
        bot_token = "7938737812:AAFiJZLaiImXRICS53p4TKcvNepP6vpnwSs"
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": "-1002375937245",
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(api_url, data=data)

        if not response.ok:
            print(f"Telegram API error: {response.text}")
            return False

        return True
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False


def notify_view(f):
    """Декоратор для отправки уведомлений"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            path = request.path
            ip_address = get_client_ip()

            # Определяем тип просмотра и детали
            view_type = "расписания"
            details = ""

            if 'group' in path:
                group_name = kwargs.get('group_name', '')
                view_type = f"расписания группы"
                details = f"Группа: <b>{group_name}</b>"
            elif 'teacher' in path:
                teacher_name = kwargs.get('teacher_name', '')
                view_type = f"расписания преподавателя"
                details = f"Преподаватель: <b>{teacher_name}</b>"
            elif 'room' in path:
                room_name = kwargs.get('room_name', '')
                view_type = f"расписания аудитории"
                details = f"Аудитория: <b>{room_name}</b>"
            elif 'free_rooms' in path:
                view_type = "списка свободных аудиторий"

            week = request.args.get('week', 'текущая')

            message = (
                f"👀 <b>Просмотр {view_type}</b>\n\n"
                f"🕒 Время: {timestamp}\n"
                f"🌐 IP: {ip_address}\n"
                f"📅 Неделя: {week}\n"
            )

            if details:
                message += f"{details}\n"

            send_notification(message)

        except Exception as e:
            print(f"Error in notification wrapper: {e}")

        return f(*args, **kwargs)

    return decorated_function