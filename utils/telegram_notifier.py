# utils/telegram_notifier.py
from flask import request, current_app
from functools import wraps
from datetime import datetime
import requests
import socket
import netifaces


def get_real_ip():
    """Получение реального IP-адреса"""
    try:
        # Получаем список всех сетевых интерфейсов
        interfaces = netifaces.interfaces()

        for interface in interfaces:
            # Пропускаем loopback
            if interface.startswith('lo'):
                continue

            addrs = netifaces.ifaddresses(interface)
            # Ищем IPv4 адреса
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    # Пропускаем локальные адреса
                    if not ip.startswith('127.'):
                        if request.environ.get('REMOTE_PORT'):
                            return f"{ip}:{request.environ.get('REMOTE_PORT')}"
                        return ip
    except:
        pass

    # Запасной вариант - получаем IP через подключение
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if request.environ.get('REMOTE_PORT'):
            return f"{ip}:{request.environ.get('REMOTE_PORT')}"
        return ip
    except:
        pass

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
            client_ip = get_real_ip()
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
            endpoint = request.endpoint if request.endpoint else 'Unknown'

            message = (
                f"👀 <b>Просмотр {view_type}</b>\n\n"
                f"🕒 Время: {timestamp}\n"
                f"🌐 IP клиента: {client_ip}\n"
                f"💻 Устройство: {system}\n"
                f"🌍 Браузер: {browser}\n"
                f"🔗 Страница: {endpoint}\n"
                f"📅 Неделя: {week}\n"
            )

            if details:
                message += f"{details}\n"

            send_notification(message)

        except Exception as e:
            print(f"Error in notification wrapper: {e}")

        return f(*args, **kwargs)

    return decorated_function