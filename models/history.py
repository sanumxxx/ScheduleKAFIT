from utils.decorators import admin_required
from flask_login import login_required
import os
import json
from datetime import datetime
from flask import request, Blueprint, render_template, redirect, url_for, session, flash

bp = Blueprint('history', __name__, url_prefix='/history')

# models/history.py


class TimetableHistory:
    def __init__(self, history_file='data/history.json'):
        self.history_file = history_file

    def format_lesson_data(self, lesson):
        """Форматирование данных пары для записи в историю"""
        if not lesson:
            return None

        return {
            'subject': lesson.get('subject', ''),
            'type': lesson.get('type', ''),
            'teachers': [t.get('teacher_name', '') for t in lesson.get('teachers', [])],
            'auditories': [a.get('auditory_name', '') for a in lesson.get('auditories', [])],
            'subgroup': lesson.get('subgroup', 0)
        }

    def add_record(self, change_type, data):
        """Добавление записи в историю"""
        try:
            history = self.read_history()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Форматируем данные о парах
            old_lessons = [self.format_lesson_data(lesson) for lesson in data.get('old_lessons', [])]
            new_lessons = [self.format_lesson_data(lesson) for lesson in data.get('lessons', [])]

            record = {
                'timestamp': timestamp,
                'type': change_type,
                'editor_ip': data.get('editor_ip'),
                'group': data.get('group_name'),
                'week': data.get('week'),
                'day': data.get('day'),
                'time': data.get('time'),
                'old_data': old_lessons,
                'new_data': new_lessons
            }

            history.append(record)
            self.save_history(history)
            return True
        except Exception as e:
            print(f"Error adding history record: {e}")
            return False

    def get_records(self, filters=None):
        """Получение записей истории с фильтрацией"""
        try:
            history = self.read_history()

            if not filters:
                return history

            filtered = history

            if 'group' in filters:
                filtered = [r for r in filtered if r['group'] == filters['group']]
            if 'week' in filters:
                filtered = [r for r in filtered if str(r['week']) == str(filters['week'])]
            if 'date_from' in filters:
                filtered = [r for r in filtered if r['timestamp'] >= filters['date_from']]
            if 'date_to' in filters:
                filtered = [r for r in filtered if r['timestamp'] <= filters['date_to']]

            return filtered
        except Exception as e:
            print(f"Error getting history records: {e}")
            return []

    def read_history(self):
        """Чтение истории из файла"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error reading history: {e}")
            return []

    def save_history(self, history):
        """Сохранение истории в файл"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving history: {e}")
            return False


# routes/history.py
@bp.route('/history')
@login_required
@admin_required
def view_history():
    """Просмотр истории изменений"""
    history_handler = TimetableHistory()

    # Получаем параметры фильтрации
    filters = {
        'group': request.args.get('group'),
        'week': request.args.get('week'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to')
    }

    # Фильтруем пустые значения
    filters = {k: v for k, v in filters.items() if v}

    # Получаем записи истории
    records = history_handler.get_records(filters)

    return render_template('timetable/history.html',
                           records=records,
                           filters=filters)