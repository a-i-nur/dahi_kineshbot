FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY db ./db
COPY pics ./pics
COPY docker/entrypoint.sh ./docker/entrypoint.sh
COPY .env.example ./.env.example

RUN chmod +x ./docker/entrypoint.sh

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["python", "-m", "app.main"]
