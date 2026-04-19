#!/usr/bin/env sh
set -eu

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required"
  exit 1
fi

if [ -z "${BOT_TOKEN:-}" ]; then
  echo "BOT_TOKEN is required"
  exit 1
fi

echo "Waiting for PostgreSQL..."
python -m app.bootstrap_db

echo "Starting bot..."
exec "$@"
