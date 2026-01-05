#!/bin/bash

# Скрипт обновления Dazino Casino на сервере
# Использование: ./update.sh

set -e

echo "🔄 Обновление Dazino Casino..."

# Переходим в директорию проекта
cd /opt/casino/casino-slot

# Сохраняем текущую версию для бэкапа
BACKUP_DIR="/opt/casino/backups/$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p $BACKUP_DIR

echo "📦 Создаем бэкап..."
sudo docker-compose exec db pg_dump -U casino_user casino_db > $BACKUP_DIR/database_backup.sql 2>/dev/null || echo "Бэкап БД не удался"

# Обновляем код из Git
echo "📥 Обновляем код из репозитория..."
git fetch origin
git pull origin master

# Пересобираем и перезапускаем контейнеры
echo "🔨 Пересобираем контейнеры..."
sudo docker-compose down
sudo docker-compose build --no-cache

echo "🚀 Запускаем обновленные контейнеры..."
sudo docker-compose up -d

# Ожидаем запуска
echo "⏳ Ожидаем запуска сервисов..."
sleep 30

# Проверяем здоровье
echo "🔍 Проверяем здоровье приложения..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Приложение запущено успешно!"
else
    echo "❌ Приложение не отвечает. Проверяем логи..."
    sudo docker-compose logs --tail=50 app
    exit 1
fi

# Очищаем старые образы
echo "🧹 Очищаем старые Docker образы..."
sudo docker image prune -f

echo "✅ Обновление завершено!"
echo ""
echo "📊 Статус:"
sudo docker-compose ps
echo ""
echo "🌐 Сайт доступен по адресу: https://your-domain.com"
echo "📝 Последние изменения:"
git log --oneline -5
