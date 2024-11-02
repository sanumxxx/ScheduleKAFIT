# services/json_handler.py
import json
import os
from datetime import datetime
import shutil
from config.config import Config
import re


class TimetableHandler:
    def __init__(self):
        self.timetable_file = Config.TIMETABLE_FILE
        self.backup_dir = Config.BACKUP_DIR

    # services/json_handler.py
    # services/json_handler.py
    def read_timetable(self):
        """Чтение расписания из JSON файла"""
        try:
            if os.path.exists(self.timetable_file):
                with open(self.timetable_file, 'r', encoding='cp1251') as file:
                    content = file.read()

                    # Заменяем проблемные escape-последовательности
                    content = content.replace('\\', '/')

                    try:
                        data = json.loads(content)
                        # Выводим первые 100 символов для проверки
                        print("Успешно загружено. Начало данных:", str(data)[:100])
                        if isinstance(data, dict) and 'timetable' in data:
                            return data['timetable']
                        elif isinstance(data, list):
                            return data
                    except json.JSONDecodeError as e:
                        # Выводим контекст ошибки
                        pos = e.pos
                        print(f"Ошибка на позиции {pos}")
                        print(f"Контекст: {content[max(0, pos - 50):min(len(content), pos + 50)]}")
                        return []
            else:
                print(f"Файл не найден: {self.timetable_file}")
                return []

        except Exception as e:
            print(f"Неожиданная ошибка: {str(e)}")
            print(f"Тип ошибки: {type(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def save_timetable(self, data):
        """Сохранение расписания в JSON файл"""
        # Создаем резервную копию
        self._create_backup()

        try:
            with open(self.timetable_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {str(e)}")
            return False

    def _create_backup(self):
        """Создание резервной копии файла расписания"""
        if os.path.exists(self.timetable_file):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'timetable_backup_{timestamp}.json')
            shutil.copy2(self.timetable_file, backup_file)

    def get_group_timetable(self, group_name):
        """Получение расписания конкретной группы"""
        data = self.read_timetable()
        for group_data in data.get('timetable', []):
            for group in group_data.get('groups', []):
                if group.get('group_name') == group_name:
                    return group
        return None

    def update_lesson(self, group_name, day_index, lesson_data):
        """Обновление информации о занятии"""
        data = self.read_timetable()
        found = False

        for group_data in data.get('timetable', []):
            for group in group_data.get('groups', []):
                if group.get('group_name') == group_name:
                    if 0 <= day_index < len(group.get('days', [])):
                        group['days'][day_index]['lessons'].append(lesson_data)
                        found = True
                        break
            if found:
                break

        if found:
            return self.save_timetable(data)
        return False

    def validate_timetable_structure(self, data):
        """Валидация структуры данных расписания"""
        required_fields = {
            'timetable': list,
            'groups': list,
            'days': list,
            'lessons': list
        }

        try:
            if not isinstance(data.get('timetable'), list):
                return False

            # Проверка структуры
            for group_data in data['timetable']:
                for group in group_data.get('groups', []):
                    if not isinstance(group.get('days'), list):
                        return False

                    for day in group['days']:
                        if not isinstance(day.get('lessons'), list):
                            return False

            return True
        except Exception:
            return False