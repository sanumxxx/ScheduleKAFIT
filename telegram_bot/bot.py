import telebot
from telebot import types
import requests

TOKEN = '6897033821:AAE80aF2-Kvn3dF8CSHH_PPMDoyulJMiLoo'
BASE_URL = 'http://schedule.kafit.ru/api'
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения состояний пользователя
user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    """Обрабатывает команду /start"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Расписание группы"),
        types.KeyboardButton("Свободные аудитории")
    )
    bot.reply_to(message, "Привет! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Расписание группы")
def get_group_schedule(message):
    """Обрабатывает запрос на получение расписания группы"""
    try:
        response = requests.get(f"{BASE_URL}/groups")
        groups = response.json()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(0, len(groups), 2):
            row = [types.KeyboardButton(groups[i])]
            if i + 1 < len(groups):
                row.append(types.KeyboardButton(groups[i + 1]))
            markup.row(*row)
        markup.row(types.KeyboardButton("Назад"))
        bot.reply_to(message, "Выберите группу:", reply_markup=markup)
        user_states[message.chat.id] = 'waiting_for_group'
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: message.text == "Свободные аудитории")
def get_free_rooms(message):
    """Обрабатывает запрос на получение списка свободных аудиторий"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    for i in range(0, len(days), 2):
        markup.row(
            types.KeyboardButton(days[i]),
            types.KeyboardButton(days[i + 1] if i + 1 < len(days) else "")
        )
    markup.row(types.KeyboardButton("Назад"))
    bot.reply_to(message, "Выберите день недели:", reply_markup=markup)
    user_states[message.chat.id] = 'waiting_for_room_day'

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    if text == "Назад":
        start(message)
        user_states.pop(chat_id, None)
        return

    state = user_states.get(chat_id)

    if state == 'waiting_for_group':
        try:
            response = requests.get(f"{BASE_URL}/schedule/{text}")
            schedule_data = response.json()
            formatted_schedule = format_schedule(schedule_data)
            # Вот здесь добавляем parse_mode='MarkdownV2'
            bot.reply_to(message, formatted_schedule, parse_mode='MarkdownV2')
            start(message)
            user_states.pop(chat_id, None)
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {str(e)}")

    elif state == 'waiting_for_room_day':
        user_states[f'{chat_id}_day'] = text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        times = ["8:00-9:20", "9:30-10:50", "11:00-12:20", "12:40-14:00",
                "14:10-15:30", "15:40-17:00", "17:10-18:30", "18:40-20:00"]
        for i in range(0, len(times), 2):
            markup.row(
                types.KeyboardButton(times[i]),
                types.KeyboardButton(times[i + 1] if i + 1 < len(times) else "")
            )
        markup.row(types.KeyboardButton("Назад"))
        bot.reply_to(message, "Выберите время:", reply_markup=markup)
        user_states[chat_id] = 'waiting_for_room_time'

    elif state == 'waiting_for_room_time':
        try:
            day = user_states.get(f'{chat_id}_day')
            response = requests.get(
                f"{BASE_URL}/free-rooms",
                params={'day': day, 'time': text}
            )
            free_rooms = response.json()
            result = f"Свободные аудитории на {day}, {text}:\n\n"
            result += "\n".join(free_rooms) if free_rooms else "Свободных аудиторий нет"
            bot.reply_to(message, result)
            start(message)
            user_states.pop(chat_id, None)
            user_states.pop(f'{chat_id}_day', None)
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {str(e)}")


def format_schedule(schedule_data):
    """Форматирует расписание для отображения с улучшенным стилем"""
    if not schedule_data or 'days' not in schedule_data:
        return "Расписание не найдено"

    def escape_markdown(text):
        """Экранирует специальные символы для MarkdownV2"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    result = []
    day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

    result.append("📋 РАСПИСАНИЕ ЗАНЯТИЙ\n")

    for day in schedule_data['days']:
        day_name = day_names[day['weekday'] - 1]
        result.append("━━━━━━━━━━━━━━━━━━━━━")
        result.append(f"**{escape_markdown(day_name)}**")

        if not day.get('lessons'):
            result.append("Нет занятий\n")
            continue

        for lesson in sorted(day['lessons'], key=lambda x: x['time']):
            result.append(f"\n{lesson['time']} пара:")
            result.append(f"└ {escape_markdown(lesson['subject'])} \\({escape_markdown(lesson['type'])}\\)")

            if lesson.get('subgroup'):
                result.append(f"└ Подгруппа {lesson['subgroup']}")

            if lesson.get('teachers'):
                teachers = ", ".join(escape_markdown(t['teacher_name']) for t in lesson['teachers'])
                result.append(f"└ {teachers}")

            if lesson.get('auditories'):
                auditories = ", ".join(escape_markdown(a['auditory_name']) for a in lesson['auditories'])
                result.append(f"└ ауд\\. {auditories}")

        result.append("")

    result.append("━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(result)

if __name__ == "__main__":
    bot.infinity_polling()
