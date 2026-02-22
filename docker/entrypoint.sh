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
until pg_isready -d "$DATABASE_URL" >/dev/null 2>&1; do
  sleep 1
done

echo "Applying schema and seed..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema.sql

if [ -f db/migrations/001_add_bio_full.sql ]; then
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/001_add_bio_full.sql
fi

if [ -f db/migrations/002_add_telegram_admins.sql ]; then
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/002_add_telegram_admins.sql
fi

if [ -f db/migrations/003_author_source_and_remove_bio_short_limit.sql ]; then
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/003_author_source_and_remove_bio_short_limit.sql
fi

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/seed.sql

if [ -n "${ADMIN_USERNAMES:-}" ]; then
  echo "Applying ADMIN_USERNAMES allow-list..."
  OLD_IFS=$IFS
  IFS=','
  for raw in $ADMIN_USERNAMES; do
    username=$(echo "$raw" | tr -d '[:space:]')
    if [ -z "$username" ]; then
      continue
    fi
    case "$username" in
      @*) ;;
      *) username="@$username" ;;
    esac
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
      -c "INSERT INTO telegram_admins (tg_username, is_active) VALUES ('${username}', TRUE) ON CONFLICT (tg_username) DO UPDATE SET is_active = EXCLUDED.is_active;"
  done
  IFS=$OLD_IFS
fi

echo "Starting bot..."
exec "$@"
