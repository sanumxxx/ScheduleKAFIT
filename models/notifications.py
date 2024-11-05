# models/notification.py
from datetime import datetime
import json


class Notification:
    def __init__(self, id, title, message, type, active_from, active_until, priority='normal'):
        self.id = id
        self.title = title
        self.message = message
        self.type = type  # 'update', 'maintenance', 'info'
        self.active_from = active_from
        self.active_until = active_until
        self.priority = priority  # 'low', 'normal', 'high'
        self.features = []  # список новых функций


class NotificationManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def save_notification(self, notification):
        """Сохранение уведомления в JSON файл"""
        notifications = self.get_notifications()

        notification_dict = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'active_from': notification.active_from.isoformat(),
            'active_until': notification.active_until.isoformat(),
            'priority': notification.priority,
            'features': notification.features
        }

        # Обновляем существующее или добавляем новое
        updated = False
        for i, notif in enumerate(notifications):
            if notif['id'] == notification.id:
                notifications[i] = notification_dict
                updated = True
                break

        if not updated:
            notifications.append(notification_dict)

        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump({'notifications': notifications}, f, ensure_ascii=False, indent=2)

    def get_notifications(self):
        """Получение всех уведомлений"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('notifications', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def delete_notification(self, notification_id):
        """Удаление уведомления"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                notifications = data.get('notifications', [])

            # Фильтруем уведомления, исключая удаляемое
            updated_notifications = [n for n in notifications if n['id'] != notification_id]

            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump({'notifications': updated_notifications}, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Ошибка при удалении уведомления: {str(e)}")
            return False