# routes/timetable.py
from flask import Blueprint, render_template, jsonify, request
from services.json_handler import TimetableHandler
from flask_login import login_required

bp = Blueprint('timetable', __name__, url_prefix='/timetable')
timetable_handler = TimetableHandler()


# routes/timetable.py
# routes/timetable.py
@bp.route('/')
def index():
    """Главная страница с выбором группы/преподавателя/аудитории"""
    timetable_data = timetable_handler.read_timetable()

    groups = set()
    teachers = set()
    rooms = set()

    if isinstance(timetable_data, list):
        for data in timetable_data:
            if 'timetable' in data:
                for week in data['timetable']:
                    for group in week.get('groups', []):
                        # Добавляем группу
                        if 'group_name' in group:
                            groups.add(group['group_name'])

                        # Собираем информацию о преподавателях и аудиториях из занятий
                        for day in group.get('days', []):
                            for lesson in day.get('lessons', []):
                                # Добавляем преподавателей
                                for teacher in lesson.get('teachers', []):
                                    if teacher.get('teacher_name'):
                                        teachers.add(teacher['teacher_name'])

                                # Добавляем аудитории
                                for auditory in lesson.get('auditories', []):
                                    if auditory.get('auditory_name'):
                                        rooms.add(auditory['auditory_name'])

    return render_template('timetable/index.html',
                           groups=sorted(list(groups)),
                           teachers=sorted(list(teachers)),
                           rooms=sorted(list(rooms)))


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





