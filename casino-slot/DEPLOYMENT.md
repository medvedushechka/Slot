# 🎰 Dazino Casino - Production Deployment

## 📋 Требования к серверу

- **ОС:** Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM:** Минимум 2GB, рекомендуется 4GB+
- **CPU:** Минимум 2 ядра, рекомендуется 4+
- **Диск:** Минимум 20GB SSD
- **ПО:** Docker, Docker Compose, Git

## 🚀 Быстрое развертывание

### 1. Подготовка сервера

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Устанавливаем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER
```

### 2. Развертывание проекта

```bash
# Клонируем репозиторий
git clone https://github.com/medvedushechka/Slot.git
cd Slot

# Делаем скрипт развертывания исполняемым
chmod +x deploy.sh

# Запускаем развертывание
./deploy.sh
```

### 3. Настройка домена

1. **DNS настройки:**
   ```
   A-запись: your-domain.com → IP_адрес_сервера
   A-запись: www.your-domain.com → IP_адрес_сервера
   ```

2. **Настройка SSL:**
   ```bash
   # Для Let's Encrypt (рекомендуется)
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

3. **Обновление nginx.conf:**
   - Замените `your-domain.com` на ваш домен
   - Укажите пути к SSL сертификатам

## 🐳 Docker Компоненты

### Сервисы:
- **app:** Основное приложение FastAPI
- **db:** PostgreSQL база данных
- **redis:** Redis для кэширования
- **nginx:** Reverse proxy и статические файлы

### Порты:
- **80:** HTTP (редирект на HTTPS)
- **443:** HTTPS
- **5432:** PostgreSQL (внутренний)
- **6379:** Redis (внутренний)
- **8000:** FastAPI (внутренний)

## 📊 Мониторинг

### Health Check:
```bash
curl https://your-domain.com/health
```

### Логи:
```bash
# Логи приложения
sudo docker-compose logs -f app

# Логи Nginx
sudo docker-compose logs -f nginx

# Логи базы данных
sudo docker-compose logs -f db
```

### Статус:
```bash
sudo docker-compose ps
```

## 🔧 Обслуживание

### Обновление:
```bash
cd /opt/casino/casino-slot
git pull origin master
sudo docker-compose up -d --build
```

### Перезапуск:
```bash
# Перезапустить все сервисы
sudo docker-compose restart

# Перезапустить только приложение
sudo docker-compose restart app
```

### Остановка:
```bash
sudo docker-compose down
```

## 🔒 Безопасность

### Базовая настройка:
1. **Изменить пароли по умолчанию** в docker-compose.yml
2. **Настроить firewall** (только порты 80, 443)
3. **Использовать SSL** сертификаты
4. **Регулярные обновления** системы

### Firewall:
```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 📈 Масштабирование

### Вертикальное масштабирование:
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### Горизонтальное масштабирование:
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 3
```

## 🚨 Поиск и устранение проблем

### Частые проблемы:

1. **Сайт не доступен:**
   ```bash
   # Проверяем статус контейнеров
   sudo docker-compose ps
   
   # Проверяем логи
   sudo docker-compose logs app
   ```

2. **База данных не подключается:**
   ```bash
   # Проверяем доступ к БД
   sudo docker-compose exec app python -c "
   from database import engine
   print(engine.url)
   "
   ```

3. **SSL ошибки:**
   ```bash
   # Проверяем сертификаты
   sudo openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout
   ```

### Резервное копирование:
```bash
# База данных
sudo docker-compose exec db pg_dump -U casino_user casino_db > backup.sql

# Восстановление
sudo docker-compose exec -T db psql -U casino_user casino_db < backup.sql
```

## 📞 Поддержка

- **GitHub:** https://github.com/medvedushechka/Slot
- **Документация:** https://github.com/medvedushechka/Slot/wiki
- **Issues:** https://github.com/medvedushechka/Slot/issues

---

**⚠️ Важно:** Перед развертыванием на production убедитесь, что все конфигурационные файлы настроены правильно, особенно пароли и доменные имена!
