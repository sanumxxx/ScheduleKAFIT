# 📅 Система управления расписанием занятий

![Лицензия](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask Version](https://img.shields.io/badge/flask-2.0%2B-green)

Веб-приложение для управления расписанием учебных занятий, позволяющее эффективно организовать учебный процесс.

## ✨ Возможности

- 📊 **Просмотр расписания**
  - Отображение занятий по дням недели
  - Фильтрация по преподавателям и группам
  - Адаптивный интерфейс для всех устройств

- 🏫 **Управление аудиториями**
  - Поиск свободных аудиторий
  - Отслеживание занятости помещений
  - Предотвращение конфликтов расписания

- 👨‍🏫 **Работа с преподавателями**
  - Просмотр нагрузки преподавателей
  - Анализ занятости
  - Удобное управление заменами

- 🔒 **Административная панель**
  - Создание и редактирование расписания
  - Управление пользователями
  - Система уведомлений об изменениях

## 🚀 Быстрый старт

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/yourusername/timetable-system.git
cd timetable-system
```

2. **Создайте виртуальное окружение**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. **Установите зависимости**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения**
```bash
cp .env.example .env
# Отредактируйте .env файл, указав необходимые параметры
```

5. **Запустите приложение**
```bash
flask run
```

## 📦 Технологии

- **Backend**: Python, Flask
- **Frontend**: HTML, TailwindCSS, JavaScript
- **База данных**: SQLite/PostgreSQL
- **Деплой**: Docker, Gunicorn

## 🎯 Структура проекта

```
timetable-system/
├── app/
│   ├── static/
│   ├── templates/
│   ├── models/
│   ├── routes/
│   └── utils/
├── config/
├── tests/
├── venv/
├── .env
├── requirements.txt
└── README.md
```

## 📝 Конфигурация

Основные настройки приложения находятся в файле `.env`:

```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db
```

## 🔧 Разработка

Для запуска в режиме разработки:

```bash
flask run --debug
```

Для запуска тестов:

```bash
pytest
```

## 🌐 Деплой

1. Соберите Docker образ:
```bash
docker build -t timetable-system .
```

2. Запустите контейнер:
```bash
docker run -d -p 8000:8000 timetable-system
```

## 📄 API Документация

API документация доступна по адресу `/api/docs` после запуска приложения.

## 📫 Контакты

- Телеграм: [@honcharov_sans](https://t.me/honcharov_sans)
- Email: sanumxxx@yandex.ru

## ⚖️ Лицензия
Данное программное обеспечение является проприетарным и защищено авторским правом. Любое несанкционированное использование, модификация, распространение или продажа строго запрещены.


---

<p align="center">Made with ❤️ by Alexandr Honcharov</p>
