# Образ Python 3.11
FROM python:3.11-slim

# Робоча директорія
WORKDIR /app

# Копіюємо файли
COPY requirements.txt .
COPY main.py .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Порт для Render
ENV PORT=10000

# Команда старту
CMD ["python", "main.py"]
