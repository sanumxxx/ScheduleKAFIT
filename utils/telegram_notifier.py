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


def format_lesson_info(lesson):
    """Компактное форматирование информации о паре"""
    return {
        'subject': lesson.get('subject', ''),
        'teacher': lesson.get('teachers', [{}])[0].get('teacher_name', ''),
        'room': lesson.get('auditories', [{}])[0].get('auditory_name', ''),
        'type': lesson.get('type', ''),
        'subgroup': lesson.get('subgroup', 0)
    }


def send_notification(message, theme=None):
    """
    Отправка уведомлений в Telegram с указанием темы
    theme: 'changes' для изменений расписания, 'visits' для просмотров
    """
    try:
        bot_token = "7938737812:AAFiJZLaiImXRICS53p4TKcvNepP6vpnwSs"
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # ID тем в Telegram
        themes = {
            'changes': 321,  # ID темы для изменений
            'visits': 323  # ID темы для просмотров
        }

        data = {
            "chat_id": "-1002375937245",
            "text": message,
            "parse_mode": "HTML"
        }

        # Добавляем ID темы, если она указана
        if theme and theme in themes:
            data["message_thread_id"] = themes[theme]

        response = requests.post(api_url, data=data)

        if not response.ok:
            print(f"Telegram API error: {response.text}")
            return False

        return True
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False


def notify_view(f):
    """Декоратор для отправки уведомлений о просмотрах"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            path = request.path
            client_ip = get_client_ip()
            browser, system = get_browser_info()
            referer = request.headers.get('Referer', 'Прямой переход')
            host = request.headers.get('Host', 'Неизвестный хост')

            # Определяем тип просмотра и детали
            view_type = "расписания"
            details = ""
            emoji = "👀"

            if 'teacher' in path:
                teacher_name = kwargs.get('teacher_name', '')
                view_type = f"расписания преподавателя"
                details = (
                    f"👨‍🏫 Преподаватель: <b>{teacher_name}</b>\n"
                    f"🔍 URL: {host}{path}\n"
                    f"↩️ Источник перехода: {referer}"
                )
                emoji = "👨‍🏫"
            elif 'group' in path:
                group_name = kwargs.get('group_name', '')
                view_type = f"расписания группы"
                details = f"Группа: <b>{group_name}</b>"
                emoji = "👥"
            elif 'room' in path:
                room_name = kwargs.get('room_name', '')
                view_type = f"расписания аудитории"
                details = f"Аудитория: <b>{room_name}</b>"
                emoji = "🚪"
            elif 'free_rooms' in path:
                view_type = "списка свободных аудиторий"
                emoji = "🔍"

            week = request.args.get('week', 'текущая')

            message = (
                f"{emoji} <b>Просмотр {view_type}</b>\n\n"
                f"🕒 Время: {timestamp}\n"
                f"🌐 IP: {client_ip}\n"
                f"💻 ОС: {system}\n"
                f"🌍 Браузер: {browser}\n"
                f"📅 Неделя: {week}\n"
            )

            if details:
                message += f"\n{details}\n"

            # Отправляем в тему просмотров
            send_notification(message, theme='visits')

        except Exception as e:
            print(f"Error in notification wrapper: {e}")
            import traceback
            print(traceback.format_exc())

        return f(*args, **kwargs)

    return decorated_function


def send_lesson_change_notification(action, group_name, weekday, time_slot, week_number, lesson_data,
                                    old_lesson_data=None, editor_ip=None):
    """Отправка уведомления об изменении расписания"""
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
    day_name = days[weekday - 1] if 0 < weekday <= len(days) else f"День {weekday}"

    week_str = f"Неделя {week_number}" if week_number else "Текущая неделя"

    time_slots = [
        '08:00-09:20', '09:30-10:50', '11:00-12:20', '12:40-14:00',
        '14:10-15:30', '15:40-17:00', '17:10-18:30', '18:40-20:00'
    ]
    time_str = time_slots[time_slot - 1] if isinstance(time_slot, int) and 0 < time_slot <= len(time_slots) else str(
        time_slot)

    if action == 'create':
        info = format_lesson_info(lesson_data)
        message = (
            f"➕ <b>Добавлена пара</b>\n\n"
            f"📅 {week_str}\n"
            f"👥 Группа: {group_name}\n"
            f"📍 {day_name}, {time_str}\n\n"
            f"📚 Предмет: {info['subject']}\n"
            f"👨‍🏫 Преподаватель: {info['teacher']}\n"
            f"🚪 Аудитория: {info['room']}\n"
            f"📝 Тип: {info['type']}"
        )
        if info['subgroup']:
            message += f"\n👥 Подгруппа: {info['subgroup']}"

    elif action == 'update':
        old = format_lesson_info(old_lesson_data)
        new = format_lesson_info(lesson_data)

        message = (
            f"✏️ <b>Изменена пара</b>\n\n"
            f"📅 {week_str}\n"
            f"👥 Группа: {group_name}\n"
            f"📍 {day_name}, {time_str}\n\n"
        )

        if old['subject'] != new['subject']:
            message += f"📚 Предмет: {old['subject']} ➜ {new['subject']}\n"
        if old['teacher'] != new['teacher']:
            message += f"👨‍🏫 Преподаватель: {old['teacher']} ➜ {new['teacher']}\n"
        if old['room'] != new['room']:
            message += f"🚪 Аудитория: {old['room']} ➜ {new['room']}\n"
        if old['type'] != new['type']:
            message += f"📝 Тип: {old['type']} ➜ {new['type']}\n"
        if old['subgroup'] != new['subgroup']:
            message += f"👥 Подгруппа: {old['subgroup'] or 'общая'} ➜ {new['subgroup'] or 'общая'}"

    elif action == 'delete':
        info = format_lesson_info(lesson_data)
        message = (
            f"❌ <b>Удалена пара</b>\n\n"
            f"📅 {week_str}\n"
            f"👥 Группа: {group_name}\n"
            f"📍 {day_name}, {time_str}\n\n"
            f"📚 Предмет: {info['subject']}\n"
            f"👨‍🏫 Преподаватель: {info['teacher']}\n"
            f"🚪 Аудитория: {info['room']}\n"
            f"📝 Тип: {info['type']}"
        )
        if info['subgroup']:
            message += f"\n👥 Подгруппа: {info['subgroup']}"

    if editor_ip:
        message += f"\n\n🌐 IP редактора: {editor_ip}"
    message += f"\n🕒 Время: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"

    # Отправляем в тему изменений
    return send_notification(message, theme='changes')

def notify_lesson_change(action='update'):
    """Декоратор для отправки уведомлений об изменениях в расписании"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return f(*args, **kwargs)

                group_name = data.get('group_name')
                day = data.get('day')
                time = data.get('time')
                week = data.get('week')
                lessons = data.get('lessons', [])
                old_lessons = data.get('old_lessons', [])

                # Получаем временной слот
                time_slots = [
                    '08:00', '09:30', '11:00',
                    '12:40', '14:10', '15:40',
                    '17:10', '18:40'
                ]
                time_slot = time_slots[time - 1] if 0 < time <= len(time_slots) else f"Пара {time}"

                # Определяем тип операции
                if not old_lessons and lessons:
                    action = 'create'
                elif not lessons and old_lessons:
                    action = 'delete'
                else:
                    action = 'update'

                # Отправляем уведомления
                for i, lesson in enumerate(lessons or old_lessons):
                    old_lesson = old_lessons[i] if i < len(old_lessons) and action == 'update' else None
                    send_lesson_change_notification(
                        action=action,
                        group_name=group_name,
                        weekday=day,
                        time_slot=time_slot,
                        week_number=week,
                        lesson_data=lesson,
                        old_lesson_data=old_lesson,
                        editor_ip=get_client_ip()
                    )

            except Exception as e:
                print(f"Error in notification wrapper: {e}")

            return f(*args, **kwargs)
        return decorated_function
    return decorator