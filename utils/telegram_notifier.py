# utils/telegram_notifier.py
from flask import request, current_app
from functools import wraps
from datetime import datetime
import requests


def get_client_ip():
    """Получение реального IP клиента из заголовков nginx"""
    # Проверяем заголовки в порядке приоритета
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Берем первый IP из списка (реальный IP клиента)
        return forwarded_for.split(',')[0].strip()

    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip

    return request.remote_addr


def get_browser_info():
    """Получение информации о браузере"""
    user_agent = request.headers.get('User-Agent', '').lower()
    browser = "Неизвестно"
    system = "Неизвестно"

    if 'edge' in user_agent:
        browser = "Edge"
    elif 'chrome' in user_agent:
        browser = "Chrome"
    elif 'firefox' in user_agent:
        browser = "Firefox"
    elif 'safari' in user_agent:
        browser = "Safari"
    elif 'opera' in user_agent:
        browser = "Opera"

    if 'windows' in user_agent:
        system = "Windows"
    elif 'android' in user_agent:
        system = "Android"
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        system = "iOS"
    elif 'linux' in user_agent:
        system = "Linux"
    elif 'macintosh' in user_agent:
        system = "MacOS"

    return browser, system


def send_notification(message):
    """Отправка уведомлений в Telegram"""
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
            client_ip = get_client_ip()
            browser, system = get_browser_info()

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

            # Добавляем информацию о всех заголовках для отладки
            headers_info = "\n\nЗаголовки запроса:\n"
            for header, value in request.headers.items():
                headers_info += f"{header}: {value}\n"

            message = (
                f"👀 <b>Просмотр {view_type}</b>\n\n"
                f"🕒 Время: {timestamp}\n"
                f"🌐 IP клиента: {client_ip}\n"
                f"💻 Устройство: {system}\n"
                f"🌍 Браузер: {browser}\n"
                f"📅 Неделя: {week}\n"
            )

            if details:
                message += f"{details}\n"

            # Временно добавляем отладочную информацию
            print("Debug headers:", headers_info)

            send_notification(message)

        except Exception as e:
            print(f"Error in notification wrapper: {e}")

        return f(*args, **kwargs)

    return decorated_function