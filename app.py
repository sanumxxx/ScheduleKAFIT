from flask import Flask, redirect, url_for
from config.config import Config
from flask_login import LoginManager, UserMixin
from routes import timetable, auth, api
import os



from routes.auth import init_login_manager


# Заглушка для пользователя
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    init_login_manager(app)

    # Добавляем user_loader
    @login_manager.user_loader
    def load_user(user_id):
        return User(user_id)

    # Регистрация blueprints
    app.register_blueprint(timetable.bp)
    app.register_blueprint(auth.bp)

    app.register_blueprint(api.bp)

    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found_error(error):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        return "Internal server error", 500

    # Маршрут главной страницы
    @app.route('/')
    def index():
        return redirect(url_for('timetable.index'))

    return app


# Создание необходимых директорий при запуске
def create_directories():
    directories = [
        'data',
        'data/backup',
        'static',
        'static/css',
        'static/js',
        'templates',
        'templates/auth',
        'templates/timetable'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


if __name__ == '__main__':
    create_directories()
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)