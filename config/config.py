# config/config.py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env'))


class Config:
    # Основные настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    DEBUG = os.environ.get('FLASK_DEBUG', True)

    # Пути к файлам данных
    DATA_DIR = os.path.join(basedir, '../data')
    TIMETABLE_FILE = os.path.join(DATA_DIR, 'timetable.json')
    BACKUP_DIR = os.path.join(DATA_DIR, 'backup')

    # Создаем директории если их нет
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)