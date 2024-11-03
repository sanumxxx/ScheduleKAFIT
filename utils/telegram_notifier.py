# utils/telegram_notifier.py
from flask import request, current_app
from functools import wraps
from datetime import datetime
import requests
import socket
import json
import urllib.request


def get_real_ip():
    """Получение реального IP пользователя"""
    try:
        # Пробуем получить IP через сервис ipinfo.io
        with urllib.request.urlopen('https://ipinfo.io/json') as response:
            data = json.loads(response.read())
            return data['ip']
    except:
        try:
            # Резервный вариант через api.ipify.org
            with urllib.request.urlopen('https://api.ipify.org?format=json') as response:
                data = json.loads(response.read())
                return data['ip']
        except:
            # Если не удалось получить IP через API, используем локальный IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip == '127.0.0.1':
                # Пытаемся получить реальный локальный IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(('8.8.8.8', 80))
                    local_ip = s.getsockname()[0]
                except:
                    pass
                finally:
                    s.close()
            return local_ip


def send_notification(message):
    """
    Отправка уведомлений в Telegram
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


def get_user_location():
    """Получение местоположения пользователя по IP"""
    try:
        with urllib.request.urlopen('https://ipinfo.io/json') as response:
            data = json.loads(response.read())
            return f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
    except:
        return "Unknown"


def notify_view(f):
    """Декоратор для отправки уведомлений"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            path = request.path
            real_ip = get_real_ip()
            location = get_user_location()

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
                f"🌐 IP: {real_ip}\n"
                f"📍 Местоположение: {location}\n"
                f"📅 Неделя: {week}\n"
            )

            if details:
                message += f"{details}\n"

            send_notification(message)

        except Exception as e:
            print(f"Error in notification wrapper: {e}")

        return f(*args, **kwargs)

    return decorated_function