class NotificationDisplay {
    constructor() {
        this.container = null;
        this.storageKey = 'seenNotifications';
        this.checkInterval = 5 * 60 * 1000; // 5 минут
    }

    init() {
        this._createContainer();
        this._checkNotifications();

        // Периодическая проверка новых уведомлений
        setInterval(() => this._checkNotifications(), this.checkInterval);
    }

    _createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notifications-container';
        this.container.className = 'fixed top-4 right-4 max-w-md z-50 space-y-4';
        document.body.appendChild(this.container);
    }

    _getSeenNotifications() {
        const seen = localStorage.getItem(this.storageKey);
        return seen ? JSON.parse(seen) : {};
    }

    _markAsSeen(notificationId) {
        const seen = this._getSeenNotifications();
        seen[notificationId] = Date.now();
        localStorage.setItem(this.storageKey, JSON.stringify(seen));
    }

    async _checkNotifications() {
        try {
            const response = await fetch('/secret-notifications/api/active');
            const notifications = await response.json();

            const seen = this._getSeenNotifications();

            notifications.forEach(notification => {
                if (!seen[notification.id]) {
                    this._showNotification(notification);
                }
            });
        } catch (error) {
            console.error('Ошибка при получении уведомлений:', error);
        }
    }

    _showNotification(notification) {
        const element = document.createElement('div');
        element.className = `bg-white rounded-lg shadow-lg overflow-hidden transform transition-all duration-300 ease-in-out`;

        // Добавляем цвет в зависимости от приоритета
        const borderColor = {
            high: 'border-l-4 border-red-500',
            normal: 'border-l-4 border-indigo-500',
            low: 'border-l-4 border-gray-500'
        }[notification.priority];

        element.classList.add(borderColor);

        element.innerHTML = `
            <div class="p-4">
                <div class="flex justify-between items-start">
                    <h3 class="text-lg font-medium text-gray-900">${notification.title}</h3>
                    <button class="text-gray-400 hover:text-gray-500" onclick="this.closest('.notification').remove()">
                        <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                </div>
                <p class="mt-2 text-sm text-gray-500">${notification.message}</p>
                ${notification.features && notification.features.length > 0 ? `
                    <ul class="mt-3 list-disc list-inside text-sm text-gray-600">
                        ${notification.features.map(feature => `
                            <li>${feature}</li>
                        `).join('')}
                    </ul>
                ` : ''}
                <div class="mt-4 flex justify-end">
                    <button class="text-sm text-indigo-600 hover:text-indigo-800" 
                            onclick="notificationDisplay._dismissNotification(this, '${notification.id}')">
                        Понятно
                    </button>
                </div>
            </div>
        `;

        element.classList.add('notification');
        this.container.appendChild(element);

        // Добавляем анимацию появления
        setTimeout(() => {
            element.classList.add('opacity-100', 'translate-y-0');
        }, 100);
    }

    _dismissNotification(button, notificationId) {
        const notificationElement = button.closest('.notification');
        notificationElement.classList.add('opacity-0', 'translate-y-2');

        setTimeout(() => {
            notificationElement.remove();
        }, 300);

        this._markAsSeen(notificationId);
    }
}

// Инициализация при загрузке страницы
const notificationDisplay = new NotificationDisplay();
document.addEventListener('DOMContentLoaded', () => {
    notificationDisplay.init();
});