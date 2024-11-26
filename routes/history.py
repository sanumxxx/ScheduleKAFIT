from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from models.history import TimetableHistory
from services.json_handler import TimetableHandler
from utils.decorators import admin_required
from datetime import datetime

bp = Blueprint('history', __name__, url_prefix='/history')
timetable_handler = TimetableHandler()


@bp.route('/')
@login_required
@admin_required
def view_history():
    """Просмотр истории изменений"""
    history_handler = TimetableHistory()

    # Получаем параметры фильтрации
    group = request.args.get('group')
    week = request.args.get('week')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    filters = {}
    if group: filters['group'] = group
    if week: filters['week'] = week
    if date_from: filters['date_from'] = date_from
    if date_to: filters['date_to'] = date_to

    # Получаем все группы для фильтра
    timetable_data = timetable_handler.read_timetable()
    groups = set()
    if isinstance(timetable_data, list):
        for data in timetable_data:
            if 'timetable' in data:
                for week_data in data['timetable']:
                    for group_data in week_data.get('groups', []):
                        if 'group_name' in group_data:
                            groups.add(group_data['group_name'])

    # Получаем записи истории
    records = history_handler.get_records(filters)

    return render_template('history/index.html', records=records, filters=filters, groups=sorted(list(groups)),
                           weeks=range(1, 53))  # предполагаем максимум 52 недели


@bp.route('/api/records')
@login_required
@admin_required
def get_history_records():
    """API для получения записей истории"""
    history_handler = TimetableHistory()

    # Получаем параметры фильтрации
    filters = {'group': request.args.get('group'), 'week': request.args.get('week'),
        'date_from': request.args.get('date_from'), 'date_to': request.args.get('date_to')}

    # Фильтруем пустые значения
    filters = {k: v for k, v in filters.items() if v}

    # Получаем записи
    records = history_handler.get_records(filters)

    return jsonify(records)


@bp.route('/clear')
@login_required
@admin_required
def clear_history():
    """Очистка истории (только для администраторов)"""
    try:
        history_handler = TimetableHistory()
        history_handler.save_history([])  # Сохраняем пустой список
        flash('История успешно очищена', 'success')
    except Exception as e:
        flash(f'Ошибка при очистке истории: {str(e)}', 'error')

    return redirect(url_for('history.view_history'))
