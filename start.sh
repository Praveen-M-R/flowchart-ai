#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Apply database migrations
python manage.py migrate

# Start the Celery worker in the background
celery -A flowchart_ai worker -l info -Q repository_tasks &

# Start the Celery beat scheduler in the background
celery -A flowchart_ai beat -l info &

# Start the Django development server
python manage.py runserver 0.0.0.0:8000