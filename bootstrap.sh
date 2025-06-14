#!/bin/bash

# Bootstrap script for development setup
echo "Setting up Guideline Ingest API..."

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

echo "Bootstrap complete!"
echo "API available at: http://localhost:8000"
echo "Admin panel: http://localhost:8000/admin"
echo "API docs: http://localhost:8000/api/docs/"