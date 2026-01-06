# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем Python зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь бэкенд
COPY backend/ .

# Копируем фронтенд
COPY frontend/ ./frontend/

# Копируем музыку в корень контейнера
COPY music/ ./music/

# Создаем директории для статических файлов
RUN mkdir -p /app/static

# Копируем статические файлы фронтенда
RUN cp -r /app/frontend/* /app/static/

# Проверяем, что музыка скопировалась правильно
RUN ls -la /app/music/ && echo "Music files found in /app/music/"

# Открываем порт
EXPOSE 8000

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
