# routes/api.py
from flask import Blueprint, jsonify, request
from services.json_handler import TimetableHandler

bp = Blueprint('api', __name__, url_prefix='/api')
timetable_handler = TimetableHandler()


def find_free_rooms(week, day, time):
    """Поиск свободных аудиторий"""
    timetable_data = timetable_handler.read_timetable()

    # Получаем все аудитории
    all_rooms = set()
    if isinstance(timetable_data, list):
        for data in timetable_data:
            if 'timetable' in data:
                for week_data in data['timetable']:
                    for group in week_data.get('groups', []):
                        for day_data in group.get('days', []):
                            for lesson in day_data.get('lessons', []):
                                for auditory in lesson.get('auditories', []):
                                    if auditory.get('auditory_name'):
                                        all_rooms.add(auditory['auditory_name'])

    # Находим занятые аудитории
    busy_rooms = set()
    if isinstance(timetable_data, list):
        for data in timetable_data:
            if 'timetable' in data:
                for week_data in data['timetable']:
                    if str(week_data.get('week_number')) == str(week):
                        for group in week_data.get('groups', []):
                            for day_data in group.get('days', []):
                                if str(day_data.get('weekday')) == str(day):
                                    for lesson in day_data.get('lessons', []):
                                        if str(lesson.get('time')) == str(time):
                                            for auditory in lesson.get('auditories', []):
                                                if auditory.get('auditory_name'):
                                                    busy_rooms.add(auditory['auditory_name'])

    # Определяем свободные аудитории
    free_rooms = sorted(list(all_rooms - busy_rooms))
    return free_rooms


@bp.route('/groups', methods=['GET'])
def get_groups():
    """Получение списка всех групп"""
    timetable_data = timetable_handler.read_timetable()
    groups = set()

    if isinstance(timetable_data, list):
        for data in timetable_data:
            if 'timetable' in data:
                for week in data['timetable']:
                    for group in week.get('groups', []):
                        groups.add(group.get('group_name'))

    return jsonify(list(sorted(groups)))


@bp.route('/schedule/<group_name>', methods=['GET'])
def get_group_schedule(group_name):
    """Получение расписания группы"""
    schedule = timetable_handler.get_group_timetable(group_name)
    return jsonify(schedule)


@bp.route('/free-rooms', methods=['GET'])
def get_free_rooms():
    """Поиск свободных аудиторий"""
    week = request.args.get('week')
    day = request.args.get('day')
    time = request.args.get('time')

    # Используем существующую логику поиска свободных аудиторий
    free_rooms = find_free_rooms(week, day, time)
    return jsonify(free_rooms)