# Используем официальный образ Python
FROM python:3.13.1

# Устанавливаем рабочую директорию
WORKDIR /Nebus

# Копируем файлы проекта в контейнер
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Указываем команду для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
