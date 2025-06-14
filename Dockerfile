FROM python:3.11-slim

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/

# Make bootstrap script executable
RUN chmod +x bootstrap.sh

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "guideline_api.wsgi:application"]