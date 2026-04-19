FROM python:3.11-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --retries 5 --default-timeout 30 -r requirements.txt

COPY app ./app
COPY db ./db
COPY pics ./pics
COPY docker/entrypoint.sh ./docker/entrypoint.sh
COPY .env.example ./.env.example

RUN chmod +x ./docker/entrypoint.sh

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["python", "-m", "app.main"]
