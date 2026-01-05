#!/bin/bash

# Скрипт развертывания Dazino Casino на сервере
# Использование: ./deploy.sh

set -e  # Выход при любой ошибке

echo "🚀 Начинаем развертывание Dazino Casino..."

# Проверка наличия Docker и Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose."
    exit 1
fi

# Создаем директорию для проекта
PROJECT_DIR="/opt/casino"
sudo mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Клонируем репозиторий
echo "📥 Клонируем репозиторий..."
if [ -d "casino-slot" ]; then
    cd casino-slot
    git pull origin master
else
    git clone https://github.com/medvedushechka/Slot.git casino-slot
    cd casino-slot
fi

# Создаем необходимые директории
echo "📁 Создаем директории..."
sudo mkdir -p music logs ssl

# Создаем SSL сертификаты (самоподписанные для начала)
if [ ! -f "ssl/cert.pem" ]; then
    echo "🔐 Создаем SSL сертификаты..."
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=RU/ST=Moscow/L=Moscow/O=Casino/CN=localhost"
fi

# Останавливаем старые контейнеры
echo "🛑 Останавливаем старые контейнеры..."
sudo docker-compose down

# Собираем и запускаем новые контейнеры
echo "🔨 Собираем образы..."
sudo docker-compose build

echo "🚀 Запускаем контейнеры..."
sudo docker-compose up -d

# Ожидаем запуска базы данных
echo "⏳ Ожидаем запуска базы данных..."
sleep 30

# Применяем миграции базы данных
echo "🗄️ Применяем миграции базы данных..."
sudo docker-compose exec app python -c "
from database import Base, engine
Base.metadata.create_all(bind=engine)
print('База данных инициализирована')
"

# Проверяем статус
echo "🔍 Проверяем статус..."
sudo docker-compose ps

echo "✅ Развертывание завершено!"
echo ""
echo "🌐 Сайт доступен по адресу: https://your-domain.com"
echo "📊 Мониторинг: http://your-domain.com/health"
echo ""
echo "📝 Полезные команды:"
echo "  Просмотр логов: sudo docker-compose logs -f app"
echo "  Перезапуск: sudo docker-compose restart app"
echo "  Остановка: sudo docker-compose down"
echo "  Обновление: cd $PROJECT_DIR/casino-slot && git pull && sudo docker-compose up -d --build"
