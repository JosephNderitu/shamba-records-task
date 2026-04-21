FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy AFTER installing requirements
COPY app/ .

# Collect static AFTER everything is copied
RUN SECRET_KEY=temp-build-key \
    POSTGRES_DB=temp \
    POSTGRES_USER=temp \
    POSTGRES_PASSWORD=temp \
    DB_HOST=localhost \
    DB_PORT=5432 \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD python manage.py migrate --noinput && \
    python manage.py create_admin && \
    gunicorn smartseason.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info