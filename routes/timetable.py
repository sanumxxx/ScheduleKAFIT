# routes/timetable.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session, json, flash, \
    get_flashed_messages
from flask.app import Flask
from config.config import Config
import tempfile
import pickle
import uuid

from services.json_handler import TimetableHandler
from flask_login import login_required, current_user
import os
from functools import wraps

bp = Blueprint('timetable', __name__, url_prefix='/timetable')
timetable_handler = TimetableHandler()
app = Flask(__name__)

app.config.from_object(Config)


# routes/timetable.py
# routes/timetable.py
@bp.route('/')
def index():
    """Главная страница"""
    timetable_data = timetable_handler.read_timetable()

    # Собираем информацию о неделях
    loaded_weeks = []
    if isinstance(timetable_data, list):
        for data in timetable_data:
            if 'timetable' in data:
                for week in data['timetable']:
                    loaded_weeks.append({
                        'week_number': week.get('week_number'),
                        'date_start': week.get('date_start'),
                        'date_end': week.get('date_end')
                    })

    # Сортируем недели по номеру
    loaded_weeks.sort(key=lambda x: x['week_number'])

    # Собираем остальные данные
    groups = set()
    teachers = set()
    rooms = set()

    if isinstance(timetable_data, list):
        for data in timetable_data:
            if 'timetable' in data:
                for week in data['timetable']:
                    for group in week.get('groups', []):
                        if 'group_name' in group:
                            groups.add(group['group_name'])

                        for day in group.get('days', []):
                            for lesson in day.get('lessons', []):
                                for teacher in lesson.get('teachers', []):
                                    if teacher.get('teacher_name'):
                                        teachers.add(teacher['teacher_name'])

                                for auditory in lesson.get('auditories', []):
                                    if auditory.get('auditory_name'):
                                        rooms.add(auditory['auditory_name'])

    return render_template('timetable/index.html',
                           is_admin=session.get('is_admin', False),
                           loaded_weeks=loaded_weeks,
                           flash_messages=get_flashed_messages(with_categories=True),
                           groups=sorted(list(groups)),
                           teachers=sorted(list(teachers)),
                           rooms=sorted(list(rooms)))


def save_temp_data(data):
    """Сохранение данных во временный файл"""
    temp_id = str(uuid.uuid4())
    temp_path = os.path.join(tempfile.gettempdir(), f'timetable_temp_{temp_id}.pkl')

    with open(temp_path, 'wb') as f:
        pickle.dump(data, f)

    return temp_id


def load_temp_data(temp_id):
    """Загрузка данных из временного файла"""
    temp_path = os.path.join(tempfile.gettempdir(), f'timetable_temp_{temp_id}.pkl')

    if os.path.exists(temp_path):
        with open(temp_path, 'rb') as f:
            data = pickle.load(f)
        return data
    return None


def remove_temp_data(temp_id):
    """Удаление временного файла"""
    temp_path = os.path.join(tempfile.gettempdir(), f'timetable_temp_{temp_id}.pkl')
    if os.path.exists(temp_path):
        os.remove(temp_path)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not session.get('is_admin'):
            flash('Доступ запрещен. Необходимы права администратора.', 'error')
            return redirect(url_for('timetable.index'))
        return f(*args, **kwargs)

    return decorated_function


@bp.route('/group/<group_name>')
def group_timetable(group_name):
    """Страница расписания группы"""
    timetable_data = timetable_handler.read_timetable()
    selected_week = request.args.get('week', None)

    # Получаем список всех недель
    weeks = []
    if isinstance(timetable_data, list):
        for timetable_item in timetable_data:  # Перебираем все элементы в корневом списке
            if 'timetable' in timetable_item:
                for week_data in timetable_item['timetable']:
                    weeks.append({
                        'week_number': week_data.get('week_number'),
                        'date_start': week_data.get('date_start'),
                        'date_end': week_data.get('date_end')
                    })

    # Сортируем недели по номеру
    weeks.sort(key=lambda x: x['week_number'])

    print("Доступные недели:", weeks)  # Отладочный вывод

    # Если неделя не выбрана, берем первую
    if not selected_week and weeks:
        selected_week = str(weeks[0].get('week_number'))

    # Расписание звонков
    time_slots = [
        {'start': '08:00', 'end': '09:20'},
        {'start': '09:30', 'end': '10:50'},
        {'start': '11:00', 'end': '12:20'},
        {'start': '12:40', 'end': '14:00'},
        {'start': '14:10', 'end': '15:30'},
        {'start': '15:40', 'end': '17:00'},
        {'start': '17:10', 'end': '18:30'},
        {'start': '18:40', 'end': '20:00'}
    ]

    day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

    # Получаем уникальные значения для выпадающих списков
    unique_values = get_unique_values(timetable_data)

    # Создаем функцию-обертку для передачи в шаблон
    def get_lessons_wrapper(timetable, day, time):
        return get_lessons(timetable, day, time, group_name, selected_week)

    print(f"Выбранная неделя: {selected_week}")  # Отладочный вывод

    return render_template('timetable/group.html',
                           group_name=group_name,
                           weeks=weeks,
                           current_week=selected_week,
                           time_slots=time_slots,
                           day_names=day_names,
                           timetable=timetable_data,
                           get_lessons=get_lessons_wrapper,
                           unique_values=unique_values)


@bp.route('/api/save_lesson', methods=['POST'])
def save_lesson():
    """API для сохранения изменений в расписании"""
    data = request.get_json()
    # Здесь будет логика сохранения
    return jsonify({"status": "success"})


def get_unique_values(timetable_data):
    """Получение уникальных значений для выпадающих списков"""
    subjects = set()
    teachers = set()
    auditories = set()

    if isinstance(timetable_data, list) and len(timetable_data) > 0:
        weeks_data = timetable_data[0].get('timetable', [])
        for week in weeks_data:
            for group in week.get('groups', []):
                for day in group.get('days', []):
                    for lesson in day.get('lessons', []):
                        subjects.add(lesson.get('subject'))
                        for teacher in lesson.get('teachers', []):
                            teachers.add(teacher.get('teacher_name'))
                        for auditory in lesson.get('auditories', []):
                            auditories.add(auditory.get('auditory_name'))

    return {
        'subjects': sorted(list(subjects)),
        'teachers': sorted(list(teachers)),
        'auditories': sorted(list(auditories)),
        'lesson_types': ['л.', 'пр.', 'лаб.']
    }


@bp.route('/api/group/<group_name>')
def get_group_timetable_json(group_name):
    """API для получения расписания группы в формате JSON"""
    timetable = timetable_handler.get_group_timetable(group_name)
    if timetable:
        return jsonify(timetable)
    return jsonify({"error": "Group not found"}), 404


def get_group_timetable(group_name, timetable_data, selected_week=None):
    """Получение расписания конкретной группы на выбранную неделю"""
    if isinstance(timetable_data, list) and len(timetable_data) > 0:
        # Получаем данные из первого элемента списка
        weeks_data = timetable_data[0].get('timetable', [])

        # Если неделя не выбрана, берем первую
        if selected_week is None and weeks_data:
            selected_week = str(weeks_data[0].get('week_number'))

        # Ищем данные для выбранной недели
        for week in weeks_data:
            if str(week.get('week_number')) == str(selected_week):
                # Ищем конкретную группу
                for group in week.get('groups', []):
                    if group.get('group_name') == group_name:
                        return week, group
    return None, None


def get_lessons(timetable_data, day, time_slot, group_name, selected_week=None):
    """Получение занятий для конкретного дня, времени и недели"""
    try:
        if isinstance(timetable_data, list):
            for timetable_item in timetable_data:
                if 'timetable' in timetable_item:
                    for week in timetable_item['timetable']:
                        # Проверяем номер недели, если он указан
                        if selected_week and str(week.get('week_number')) != str(selected_week):
                            continue

                        for group in week.get('groups', []):
                            if group.get('group_name') == group_name:
                                for day_data in group.get('days', []):
                                    if day_data.get('weekday') == day:
                                        lessons = [
                                            lesson for lesson in day_data.get('lessons', [])
                                            if lesson.get('time') == time_slot
                                        ]
                                        if lessons:
                                            print(
                                                f"Найдены занятия для группы {group_name}, день {day}, пара {time_slot}, неделя {week.get('week_number')}")
                                            return lessons
        return None
    except Exception as e:
        print(f"Ошибка в get_lessons: {str(e)}")
        return None


@bp.route('/edit/<group_name>')
@login_required
def edit_timetable(group_name):
    """Страница редактирования расписания группы"""
    timetable = timetable_handler.get_group_timetable(group_name)
    if timetable:
        return render_template('timetable/edit.html', timetable=timetable)
    return "Группа не найдена", 404


@bp.route('/api/update', methods=['POST'])
def update_timetable():
    data = request.get_json()

    try:
        group_name = data.get('group_name')
        day = data.get('day')
        time = data.get('time')
        lessons = data.get('lessons')

        print("Получены данные:", {
            "group_name": group_name,
            "day": day,
            "time": time,
            "lessons": lessons
        })

        if not all([group_name is not None, day is not None, time is not None, isinstance(lessons, list)]):
            missing = []
            if group_name is None: missing.append('group_name')
            if day is None: missing.append('day')
            if time is None: missing.append('time')
            if not isinstance(lessons, list): missing.append('lessons')
            error_msg = f"Missing required data: {', '.join(missing)}"
            print("Ошибка валидации:", error_msg)
            return jsonify({"status": "error", "error": error_msg}), 400

        # Обновляем данные
        success = timetable_handler.update_lessons(group_name, day, time, lessons)

        if success:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "error": "Failed to update timetable"}), 500

    except Exception as e:
        print(f"Error updating timetable: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route('/teacher/<teacher_name>')
def teacher_timetable(teacher_name):
    """Просмотр расписания преподавателя"""
    timetable_data = timetable_handler.read_timetable()
    selected_week = request.args.get('week', None)

    # Получаем список всех недель
    weeks = []
    if isinstance(timetable_data, list):
        for timetable_item in timetable_data:
            if 'timetable' in timetable_item:
                for week_data in timetable_item['timetable']:
                    weeks.append({
                        'week_number': week_data.get('week_number'),
                        'date_start': week_data.get('date_start'),
                        'date_end': week_data.get('date_end')
                    })

    # Сортируем недели по номеру
    weeks.sort(key=lambda x: x['week_number'])

    # Если неделя не выбрана, берем первую
    if not selected_week and weeks:
        selected_week = str(weeks[0].get('week_number'))

    # Расписание звонков
    time_slots = [
        {'start': '08:00', 'end': '09:20'},
        {'start': '09:30', 'end': '10:50'},
        {'start': '11:00', 'end': '12:20'},
        {'start': '12:40', 'end': '14:00'},
        {'start': '14:10', 'end': '15:30'},
        {'start': '15:40', 'end': '17:00'},
        {'start': '17:10', 'end': '18:30'},
        {'start': '18:40', 'end': '20:00'}
    ]

    day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

    def get_teacher_lessons(timetable, day, time):
        """Получение занятий преподавателя для конкретного дня и времени"""
        lessons_by_type = {}  # Словарь для группировки занятий по типу и предмету

        try:
            if isinstance(timetable, list):
                for data in timetable:
                    if 'timetable' in data:
                        for week in data['timetable']:
                            if selected_week and str(week.get('week_number')) != str(selected_week):
                                continue

                            for group in week.get('groups', []):
                                group_name = group.get('group_name')
                                for day_data in group.get('days', []):
                                    if day_data.get('weekday') == day:
                                        for lesson in day_data.get('lessons', []):
                                            if (lesson.get('time') == time and
                                                    any(teacher.get('teacher_name') == teacher_name
                                                        for teacher in lesson.get('teachers', []))):

                                                # Создаем ключ для группировки
                                                key = (lesson.get('subject'), lesson.get('type'),
                                                       lesson.get('auditories', [{}])[0].get('auditory_name'))

                                                if key not in lessons_by_type:
                                                    # Создаем новую запись с первой группой
                                                    lesson_copy = lesson.copy()
                                                    lesson_copy['groups'] = [group_name]
                                                    lessons_by_type[key] = lesson_copy
                                                else:
                                                    # Добавляем группу к существующей записи
                                                    lessons_by_type[key]['groups'].append(group_name)

            # Преобразуем словарь в список и сортируем группы
            result = list(lessons_by_type.values())
            for lesson in result:
                lesson['groups'].sort()

            return result if result else None

        except Exception as e:
            print(f"Ошибка в get_teacher_lessons: {str(e)}")
            return None

    return render_template('timetable/teacher.html',
                           teacher_name=teacher_name,
                           weeks=weeks,
                           current_week=selected_week,
                           time_slots=time_slots,
                           day_names=day_names,
                           timetable=timetable_data,
                           get_lessons=get_teacher_lessons)


UPLOAD_FOLDER = 'data/uploads'
MERGED_FILE = 'data/timetable.json'


@bp.route('/login', methods=['POST'])
def login():
    """Простая авторизация администратора"""
    password = request.form.get('password')
    if password == app.config['ADMIN_PASSWORD']:
        session['is_admin'] = True
        flash('Вы успешно вошли как администратор', 'success')
    else:
        flash('Неверный пароль', 'error')
    return redirect(url_for('timetable.index'))


@bp.route('/logout')
def logout():
    """Выход из админки"""
    session.pop('is_admin', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('timetable.index'))


def read_merged_file():
    """Чтение данных расписания из файла"""
    print("\n=== Чтение файла расписания ===")

    if not os.path.exists(MERGED_FILE):
        print(f"Файл не существует: {MERGED_FILE}")
        return []

    print(f"Чтение файла: {MERGED_FILE}")

    try:
        with open(MERGED_FILE, 'rb') as f:
            content = f.read()
            print(f"Размер файла: {len(content)} байт")

            # Пробуем разные кодировки
            for encoding in ['windows-1251', 'utf-8', 'utf-8-sig']:
                try:
                    decoded_content = content.decode(encoding)
                    print(f"Успешная декодировка с {encoding}")
                    data = json.loads(decoded_content)
                    print(f"JSON успешно прочитан, тип данных: {type(data)}")
                    return data
                except UnicodeDecodeError:
                    continue
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON с {encoding}: {str(e)}")
                    continue

            print("Не удалось прочитать файл ни с одной кодировкой")
            return []

    except Exception as e:
        print(f"Ошибка чтения файла: {str(e)}")
        return []

    print("=== Завершение чтения файла ===\n")


@bp.route('/upload', methods=['POST'])
@admin_required
def upload_files():
    """Загрузка файлов расписания"""
    print("\n=== Начало загрузки файлов ===")

    if 'timetable_files' not in request.files:
        print("Файлы не найдены в запросе")
        flash('Нет выбранных файлов', 'error')
        return redirect(url_for('timetable.index'))

    files = request.files.getlist('timetable_files')
    if not files:
        print("Список файлов пуст")
        flash('Нет выбранных файлов', 'error')
        return redirect(url_for('timetable.index'))

    print(f"Получено файлов: {len(files)}")
    print(f"Имена файлов: {[f.filename for f in files]}")

    new_data = []
    existing_weeks = set()
    conflicts = []

    # Загружаем существующие данные
    current_data = read_merged_file()
    print(f"Текущие данные загружены: {current_data is not None}")

    if current_data:
        if isinstance(current_data, list):
            for item in current_data:
                if 'timetable' in item:
                    for week in item['timetable']:
                        existing_weeks.add(week['week_number'])
            print(f"Найдено существующих недель: {len(existing_weeks)}")
            print(f"Номера недель: {sorted(list(existing_weeks))}")
        new_data.extend(current_data)

    # Обрабатываем новые файлы
    for file in files:
        if not file.filename:
            continue

        print(f"\nОбработка файла: {file.filename}")
        try:
            # Читаем содержимое файла
            file_content = file.read()
            print(f"Размер файла: {len(file_content)} байт")

            try:
                # Пробуем разные кодировки
                for encoding in ['windows-1251', 'utf-8', 'utf-8-sig']:
                    try:
                        content = file_content.decode(encoding)
                        print(f"Успешная декодировка с {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise UnicodeDecodeError("Не удалось определить кодировку файла")

                # Обрабатываем escape-последовательности
                content = content.replace('\\', '\\\\')

                # Парсим JSON
                file_data = json.loads(content)
                print("JSON успешно прочитан")

                if not isinstance(file_data, list):
                    print(f"Неверный формат данных. Ожидался список, получен {type(file_data)}")
                    continue

                # Проверяем недели в новом файле
                for item in file_data:
                    if 'timetable' in item:
                        for week in item['timetable']:
                            week_num = week['week_number']
                            if week_num in existing_weeks:
                                print(f"Конфликт: неделя {week_num}")
                                conflicts.append({
                                    'week': week_num,
                                    'file': file.filename,
                                    'date_start': week['date_start'],
                                    'date_end': week['date_end']
                                })
                            else:
                                new_data.append(item)
                                existing_weeks.add(week_num)
                                print(f"Добавлена неделя {week_num}")

            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {str(e)}")
                # Показываем контекст ошибки
                if hasattr(e, 'pos'):
                    start = max(0, e.pos - 50)
                    end = min(len(content), e.pos + 50)
                    print(f"Контекст ошибки: {content[start:end]}")
                raise

        except Exception as e:
            print(f"Ошибка обработки файла: {str(e)}")
            flash(f'Ошибка при обработке файла {file.filename}: {str(e)}', 'error')
            return redirect(url_for('timetable.index'))

    print(f"\nИтоги обработки:")
    print(f"Конфликтов найдено: {len(conflicts)}")
    print(f"Всего недель в новых данных: {len(new_data)}")

    # Если есть конфликты
    if conflicts:
        print("Сохранение данных во временный файл")
        temp_id = save_temp_data({
            'pending_data': new_data,
            'conflicts': conflicts
        })
        session['temp_id'] = temp_id
        return redirect(url_for('timetable.resolve_conflicts'))

    # Если конфликтов нет, сохраняем данные
    try:
        print("Сохранение объединенных данных")
        save_merged_data(new_data)
        flash('Файлы успешно загружены и объединены', 'success')
    except Exception as e:
        print(f"Ошибка сохранения: {str(e)}")
        flash(f'Ошибка при сохранении данных: {str(e)}', 'error')

    print("=== Завершение загрузки файлов ===\n")
    return redirect(url_for('timetable.index'))


@bp.route('/resolve_conflicts')
@admin_required
def resolve_conflicts():
    """Страница разрешения конфликтов"""
    temp_id = session.get('temp_id')
    if not temp_id:
        flash('Нет конфликтов для разрешения', 'info')
        return redirect(url_for('timetable.index'))

    temp_data = load_temp_data(temp_id)
    if not temp_data or 'conflicts' not in temp_data:
        flash('Данные о конфликтах не найдены', 'error')
        return redirect(url_for('timetable.index'))

    return render_template('timetable/resolve_conflicts.html', conflicts=temp_data['conflicts'])


@bp.route('/apply_resolution', methods=['POST'])
@admin_required
def apply_resolution():
    """Применение решений по конфликтам"""
    try:
        resolutions = request.json
        temp_id = session.get('temp_id')

        if not temp_id:
            return jsonify({
                'status': 'error',
                'message': 'Данные для обработки не найдены'
            }), 400

        temp_data = load_temp_data(temp_id)
        if not temp_data:
            return jsonify({
                'status': 'error',
                'message': 'Временные данные не найдены'
            }), 400

        pending_data = temp_data['pending_data']
        current_data = read_merged_file() or []

        # Обрабатываем каждую неделю согласно решению
        for week_num, action in resolutions.items():
            week_num = int(week_num)

            if action == 'merge':
                # Собираем все данные для этой недели
                all_weeks = []

                # Из текущих данных
                for item in current_data:
                    if 'timetable' in item:
                        for week in item['timetable']:
                            if week['week_number'] == week_num:
                                all_weeks.append(week)

                # Из новых данных
                for item in pending_data:
                    if 'timetable' in item:
                        for week in item['timetable']:
                            if week['week_number'] == week_num:
                                all_weeks.append(week)

                # Объединяем недели
                merged_weeks = merge_weeks(all_weeks)

                # Удаляем старые данные об этой неделе
                current_data = [
                    item for item in current_data
                    if 'timetable' not in item or
                       not any(w['week_number'] == week_num for w in item['timetable'])
                ]

                # Добавляем объединенные данные
                if merged_weeks:
                    current_data.append({'timetable': merged_weeks})

            elif action == 'skip':
                # Пропускаем новые данные
                pending_data = [
                    item for item in pending_data
                    if 'timetable' not in item or
                       not any(w['week_number'] == week_num for w in item['timetable'])
                ]
            elif action == 'replace':
                # Удаляем старые данные
                current_data = [
                    item for item in current_data
                    if 'timetable' not in item or
                       not any(w['week_number'] == week_num for w in item['timetable'])
                ]
                # Добавляем новые данные
                current_data.extend([
                    item for item in pending_data
                    if 'timetable' in item and
                       any(w['week_number'] == week_num for w in item['timetable'])
                ])

        # Объединяем оставшиеся данные
        merged_data = current_data + [
            item for item in pending_data
            if item not in current_data
        ]

        # Сохраняем результат
        save_merged_data(merged_data)

        # Очищаем временные данные
        remove_temp_data(temp_id)
        session.pop('temp_id', None)

        flash('Конфликты успешно разрешены', 'success')
        return jsonify({'status': 'success'})

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.errorhandler(Exception)
def handle_error(e):
    temp_id = session.get('temp_id')
    if temp_id:
        remove_temp_data(temp_id)
        session.pop('temp_id', None)
    return str(e), 500

def save_merged_data(data):
    """Сохранение объединенных данных"""
    # Создаем папку, если её нет
    os.makedirs(os.path.dirname(MERGED_FILE), exist_ok=True)

    # Сохраняем данные в windows-1251
    with open(MERGED_FILE, 'w', encoding='windows-1251') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@bp.route('/room/<room_name>')
def room_timetable(room_name):
    """Просмотр расписания аудитории"""
    timetable_data = timetable_handler.read_timetable()
    selected_week = request.args.get('week', None)

    # Получаем список всех недель
    weeks = []
    if isinstance(timetable_data, list):
        for timetable_item in timetable_data:
            if 'timetable' in timetable_item:
                for week_data in timetable_item['timetable']:
                    weeks.append({
                        'week_number': week_data.get('week_number'),
                        'date_start': week_data.get('date_start'),
                        'date_end': week_data.get('date_end')
                    })

    # Сортируем недели по номеру
    weeks.sort(key=lambda x: x['week_number'])

    # Если неделя не выбрана, берем первую
    if not selected_week and weeks:
        selected_week = str(weeks[0].get('week_number'))

    # Расписание звонков
    time_slots = [
        {'start': '08:00', 'end': '09:20'},
        {'start': '09:30', 'end': '10:50'},
        {'start': '11:00', 'end': '12:20'},
        {'start': '12:40', 'end': '14:00'},
        {'start': '14:10', 'end': '15:30'},
        {'start': '15:40', 'end': '17:00'},
        {'start': '17:10', 'end': '18:30'},
        {'start': '18:40', 'end': '20:00'}
    ]

    day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

    def get_room_lessons(timetable, day, time):
        """Получение занятий в аудитории для конкретного дня и времени"""
        lessons = []
        try:
            if isinstance(timetable, list):
                for data in timetable:
                    if 'timetable' in data:
                        for week in data['timetable']:
                            # Проверяем номер недели, если он указан
                            if selected_week and str(week.get('week_number')) != str(selected_week):
                                continue

                            for group in week.get('groups', []):
                                for day_data in group.get('days', []):
                                    if day_data.get('weekday') == day:
                                        for lesson in day_data.get('lessons', []):
                                            if (lesson.get('time') == time and
                                                    any(auditory.get('auditory_name') == room_name
                                                        for auditory in lesson.get('auditories', []))):
                                                # Добавляем информацию о группе к занятию
                                                lesson_with_group = lesson.copy()
                                                lesson_with_group['group_name'] = group.get('group_name')
                                                lessons.append(lesson_with_group)
            return lessons if lessons else None
        except Exception as e:
            print(f"Ошибка в get_room_lessons: {str(e)}")
            return None

    return render_template('timetable/room.html',
                           room_name=room_name,
                           weeks=weeks,
                           current_week=selected_week,
                           time_slots=time_slots,
                           day_names=day_names,
                           timetable=timetable_data,
                           get_lessons=get_room_lessons)
