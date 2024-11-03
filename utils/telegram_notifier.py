import requests
from functools import wraps
from flask import request
from datetime import datetime


def send_telegram_notification(bot_token, message):
    """
    Простая функция для отправки уведомлений в Telegram
    """
    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": "@schedule_notifications",  # Имя канала/группы
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(api_url, data=data)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False


def notify_view(bot_token):
    """
    Декоратор для отправки уведомлений при просмотре страницы
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            message = (
                f"👀 <b>Просмотр расписания</b>\n\n"
                f"🕒 Время: {timestamp}"
            )

            # Отправляем уведомление
            send_telegram_notification(bot_token, message)

            return f(*args, **kwargs)

        return wrapper

    return decorator