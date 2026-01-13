FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# системные зависимости (минимум)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir poetry

# копируем только файлы зависимостей
COPY pyproject.toml poetry.lock ./

# ставим зависимости (без установки пакета проекта)
RUN poetry install --no-interaction --no-ansi --no-root

# копируем код
COPY . .

# порт
EXPOSE 8000

# запуск
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=project_run.settings.local"]
