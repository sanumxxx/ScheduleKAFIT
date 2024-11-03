import telebot
from telebot import types
import requests
import json
from datetime import datetime

TOKEN = '6897033821:AAE80aF2-Kvn3dF8CSHH_PPMDoyulJMiLoo'
BASE_URL = 'http://schedule.kafit.ru/api'  # URL вашего сайта
bot = telebot.TeleBot(TOKEN)

# Хранение состояний пользователя
user_states = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🗓 Расписание группы")
    btn2 = types.KeyboardButton("🔍 Свободные аудитории")
    markup.add(btn1, btn2)

    bot.reply_to(message,
                 f"Привет, {message.from_user.first_name}! 👋\n"
                 f"Я помогу узнать расписание занятий.",
                 reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "🗓 Расписание группы")
def ask_group(message):
    try:
        # Получаем список групп с сайта
        response = requests.get(f"{BASE_URL}/groups")
        groups = response.json()

        # Создаем клавиатуру с группами
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(0, len(groups), 2):
            row = [types.KeyboardButton(groups[i])]
            if i + 1 < len(groups):
                row.append(types.KeyboardButton(groups[i + 1]))
            markup.row(*row)
        markup.row(types.KeyboardButton("↩️ Назад"))

        bot.reply_to(message, "Выберите группу:", reply_markup=markup)
        user_states[message.chat.id] = 'waiting_for_group'
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при получении списка групп: {str(e)}")


@bot.message_handler(func=lambda message: message.text == "🔍 Свободные аудитории")
def free_rooms_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    for i in range(0, len(days), 2):
        markup.row(
            types.KeyboardButton(days[i]),
            types.KeyboardButton(days[i + 1] if i + 1 < len(days) else "")
        )
    markup.row(types.KeyboardButton("↩️ Назад"))

    bot.reply_to(message, "Выберите день недели:", reply_markup=markup)
    user_states[message.chat.id] = 'waiting_for_room_day'


def format_schedule(schedule_data):
    """Форматирование расписания для отображения"""
    if not schedule_data or 'days' not in schedule_data:
        return "Расписание не найдено"

    result = []
    day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

    for day in schedule_data['days']:
        day_name = day_names[day['weekday'] - 1]
        result.append(f"\n📅 {day_name}")

        if not day.get('lessons'):
            result.append("Нет занятий")
            continue

        for lesson in sorted(day['lessons'], key=lambda x: x['time']):
            time_slots = [
                "8:00-9:20", "9:30-10:50", "11:00-12:20",
                "12:40-14:00", "14:10-15:30", "15:40-17:00",
                "17:10-18:30", "18:40-20:00"
            ]
            time = time_slots[lesson['time'] - 1]

            result.append(f"\n⏰ {time}")
            result.append(f"📚 {lesson['subject']}")
            result.append(f"🎓 {lesson['type']}")

            if lesson.get('subgroup'):
                result.append(f"👥 Подгруппа {lesson['subgroup']}")

            if lesson.get('teachers'):
                teachers = ", ".join(t['teacher_name'] for t in lesson['teachers'])
                result.append(f"👨‍🏫 {teachers}")

            if lesson.get('auditories'):
                auditories = ", ".join(a['auditory_name'] for a in lesson['auditories'])
                result.append(f"🚪 {auditories}")

            result.append("")

    return "\n".join(result)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    if text == "↩️ Назад":
        send_welcome(message)
        user_states.pop(chat_id, None)
        return

    state = user_states.get(chat_id)

    if state == 'waiting_for_group':
        try:
            # Получаем расписание группы
            response = requests.get(f"{BASE_URL}/schedule/{text}")
            schedule_data = response.json()

            # Форматируем и отправляем расписание
            formatted_schedule = format_schedule(schedule_data)
            bot.reply_to(message, formatted_schedule)

            # Возвращаемся в главное меню
            send_welcome(message)
            user_states.pop(chat_id, None)
        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка при получении расписания: {str(e)}")

    elif state == 'waiting_for_room_day':
        # Сохраняем выбранный день и показываем время
        user_states[f'{chat_id}_day'] = text

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        times = ["8:00-9:20", "9:30-10:50", "11:00-12:20", "12:40-14:00",
                 "14:10-15:30", "15:40-17:00", "17:10-18:30", "18:40-20:00"]

        for i in range(0, len(times), 2):
            markup.row(
                types.KeyboardButton(times[i]),
                types.KeyboardButton(times[i + 1] if i + 1 < len(times) else "")
            )
        markup.row(types.KeyboardButton("↩️ Назад"))

        bot.reply_to(message, "Выберите время:", reply_markup=markup)
        user_states[chat_id] = 'waiting_for_room_time'

    elif state == 'waiting_for_room_time':
        try:
            day = user_states.get(f'{chat_id}_day')
            # Получаем свободные аудитории
            response = requests.get(
                f"{BASE_URL}/free-rooms",
                params={'day': day, 'time': text}
            )
            free_rooms = response.json()

            # Форматируем и отправляем результат
            result = f"Свободные аудитории на {day}, {text}:\n\n"
            result += "\n".join(free_rooms) if free_rooms else "Свободных аудиторий нет"

            bot.reply_to(message, result)

            # Возвращаемся в главное меню
            send_welcome(message)
            user_states.pop(chat_id, None)
            user_states.pop(f'{chat_id}_day', None)
        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка при поиске аудиторий: {str(e)}")


# Запуск бота
if __name__ == "__main__":
    bot.infinity_polling()