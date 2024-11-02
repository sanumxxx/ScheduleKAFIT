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
    """Главная страница с выбором группы"""
    timetable_data = timetable_handler.read_timetable()
    groups = []

    if isinstance(timetable_data, list) and len(timetable_data) > 0:
        weeks_data = timetable_data[0].get('timetable', [])
        if weeks_data:
            for group in weeks_data[0].get('groups', []):
                if 'group_name' in group:
                    groups.append(group['group_name'])

    return render_template('timetable/index.html', groups=groups)


@bp.route('/group/<group_name>')
def group_timetable(group_name):
    """Страница расписания группы"""
    timetable_data = timetable_handler.read_timetable()
    selected_week = request.args.get('week', None)

    # Получаем список всех недель
    weeks = []
    if isinstance(timetable_data, list) and len(timetable_data) > 0:
        for week_data in timetable_data[0].get('timetable', []):
            weeks.append({
                'week_number': week_data.get('week_number'),
                'date_start': week_data.get('date_start'),
                'date_end': week_data.get('date_end')
            })

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
        return get_lessons(timetable, day, time, group_name)

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


def get_lessons(timetable_data, day, time_slot, group_name):
    """Получение занятий для конкретного дня и времени"""
    try:
        if isinstance(timetable_data, list) and len(timetable_data) > 0:
            weeks_data = timetable_data[0].get('timetable', [])
            for week in weeks_data:
                for group in week.get('groups', []):
                    if group.get('group_name') == group_name:
                        for day_data in group.get('days', []):
                            if day_data.get('weekday') == day:
                                lessons = [
                                    lesson for lesson in day_data.get('lessons', [])
                                    if lesson.get('time') == time_slot
                                ]
                                if lessons:
                                    print(f"Найдены занятия для группы {group_name}, день {day}, пара {time_slot}")
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
@login_required
def update_timetable():
    """API для обновления расписания"""
    data = request.get_json()

    group_name = data.get('group_name')
    day_index = data.get('day_index')
    lesson_data = data.get('lesson')

    if not all([group_name, isinstance(day_index, int), lesson_data]):
        return jsonify({"error": "Invalid data"}), 400

    success = timetable_handler.update_lesson(group_name, day_index, lesson_data)

    if success:
        return jsonify({"message": "Updated successfully"})
    return jsonify({"error": "Update failed"}), 500



