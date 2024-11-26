import json
import os
from datetime import datetime
import shutil
from config.config import Config


class TimetableHandler:
    def __init__(self):
        self.timetable_file = Config.TIMETABLE_FILE
        self.backup_dir = Config.BACKUP_DIR

    def read_timetable(self):
        """Чтение расписания из JSON файла"""
        try:
            if os.path.exists(self.timetable_file):
                with open(self.timetable_file, 'r', encoding='utf-8-sig') as file:
                    try:
                        data = json.load(file)
                        print("Данные успешно загружены")
                        return data
                    except json.JSONDecodeError as e:
                        print(f"Ошибка декодирования JSON: {e}")
                        return []
            else:
                print(f"Файл не найден: {self.timetable_file}")
                return []
        except Exception as e:
            print(f"Ошибка чтения файла: {str(e)}")
            try:
                # Пробуем другую кодировку
                with open(self.timetable_file, 'r', encoding='cp1251') as file:
                    data = json.load(file)
                    print("Данные успешно загружены (cp1251)")
                    return data
            except Exception as e2:
                print(f"Ошибка при повторной попытке: {str(e2)}")
                return []

    def save_timetable(self, data):
        """Сохранение расписания в JSON файл"""
        try:
            # Создаем резервную копию перед сохранением
            self._create_backup()

            # Сохраняем в той же кодировке, в которой читаем
            with open(self.timetable_file, 'w', encoding='utf-8-sig') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print("Данные успешно сохранены")
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {str(e)}")
            return False

    def _create_backup(self):
        """Создание резервной копии файла расписания"""
        try:
            if os.path.exists(self.timetable_file):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(self.backup_dir, f'timetable_backup_{timestamp}.json')
                # Копируем файл
                shutil.copy2(self.timetable_file, backup_file)
                print(f"Создана резервная копия: {backup_file}")
                return True
        except Exception as e:
            print(f"Ошибка создания резервной копии: {str(e)}")
            return False

    def get_group_timetable(self, group_name):
        """Получение расписания конкретной группы"""
        try:
            data = self.read_timetable()
            if isinstance(data, list) and len(data) > 0:
                weeks_data = data[0].get('timetable', [])
                for week in weeks_data:
                    for group in week.get('groups', []):
                        if group.get('group_name') == group_name:
                            return group
            return None
        except Exception as e:
            print(f"Ошибка получения расписания группы: {str(e)}")
            return None

    def update_lesson(self, group_name, day_index, lesson_data):
        """Обновление информации о занятии"""
        try:
            data = self.read_timetable()
            found = False

            if isinstance(data, list) and len(data) > 0:
                weeks_data = data[0].get('timetable', [])
                for week in weeks_data:
                    for group in week.get('groups', []):
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
        except Exception as e:
            print(f"Ошибка обновления занятия: {str(e)}")
            return False

    def update_lessons(self, group_name, day, time, new_lessons):
        """Обновление занятий в расписании"""
        try:
            print(f"Обновление занятий для группы {group_name}, день {day}, время {time}")
            print("Новые занятия:", new_lessons)

            # Читаем текущие данные
            data = self.read_timetable()
            if not data or not isinstance(data, list):
                print("Ошибка: неверный формат данных расписания")
                return False

            # Создаем резервную копию
            self._create_backup()
            print("Создана резервная копия")

            # Находим нужную группу и обновляем занятия
            found = False
            try:
                weeks_data = data[0].get('timetable', [])
                for week in weeks_data:
                    for group in week.get('groups', []):
                        if group.get('group_name') == group_name:
                            print(f"Найдена группа {group_name}")
                            for day_data in group.get('days', []):
                                if day_data.get('weekday') == day:
                                    print(f"Найден день {day}")
                                    # Удаляем существующие занятия на это время
                                    old_lessons = [lesson for lesson in day_data.get('lessons', []) if
                                        lesson.get('time') == time]
                                    print("Удаляемые занятия:", old_lessons)

                                    # Фильтруем существующие занятия
                                    day_data['lessons'] = [lesson for lesson in day_data.get('lessons', []) if
                                        lesson.get('time') != time]

                                    # Добавляем новые занятия
                                    if isinstance(new_lessons, list):
                                        day_data['lessons'].extend(new_lessons)
                                    else:
                                        print(f"Ошибка: new_lessons не является списком: {type(new_lessons)}")
                                        return False

                                    found = True
                                    print("Занятия обновлены")
                                    break
                            if found:
                                break
                    if found:
                        break
            except Exception as e:
                print(f"Ошибка при обновлении занятий: {str(e)}")
                return False

            if not found:
                print("Группа/день не найдены")
                return False

            # Сохраняем обновленные данные
            success = self.save_timetable(data)
            print("Результат сохранения:", success)
            return success

        except Exception as e:
            print(f"Ошибка в update_lessons: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

    def validate_timetable_structure(self, data):
        """Валидация структуры данных расписания"""
        try:
            if not isinstance(data, (dict, list)):
                print("Данные не являются словарем или списком")
                return False

            if isinstance(data, list):
                if not data:
                    print("Пустой список данных")
                    return False
                data = data[0]  # Берем первый элемент списка

            if 'timetable' not in data:
                print("Отсутствует ключ 'timetable'")
                return False

            timetable = data['timetable']
            if not isinstance(timetable, list):
                print("'timetable' не является списком")
                return False

            for week in timetable:
                if 'groups' not in week:
                    print("Отсутствует ключ 'groups' в неделе")
                    return False

                for group in week['groups']:
                    if 'days' not in group:
                        print("Отсутствует ключ 'days' в группе")
                        return False

                    for day in group['days']:
                        if 'lessons' not in day:
                            print("Отсутствует ключ 'lessons' в дне")
                            return False

                        if not isinstance(day['lessons'], list):
                            print("'lessons' не является списком")
                            return False

            return True
        except Exception as e:
            print(f"Ошибка валидации: {str(e)}")
            return False


class SettingsHandler:
    def __init__(self, file_path='data/settings.json'):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path))
        if not os.path.exists(self.file_path):
            self.save_settings({'ignored_rooms': []})

    def read_settings(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading settings: {str(e)}")
            return {'ignored_rooms': []}

    def save_settings(self, settings):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False
