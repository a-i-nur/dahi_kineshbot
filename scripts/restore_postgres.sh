#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/restore_postgres.sh <backup_file.sql.gz|backup_file.sql> [--yes]

Examples:
  bash scripts/restore_postgres.sh backups/dahi_kineshbot-20260421-020000.sql.gz
  bash scripts/restore_postgres.sh backups/dahi_kineshbot-20260421-020000.sql.gz --yes

What it does:
  1) Creates a safety backup before restore.
  2) Drops and recreates schema public in the target database.
  3) Restores SQL dump into the database container.
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

backup_file="$1"
auto_yes="${2:-}"

if [[ ! -f "${backup_file}" ]]; then
  echo "Backup file not found: ${backup_file}"
  exit 1
fi

if [[ "${backup_file}" != *.sql && "${backup_file}" != *.sql.gz ]]; then
  echo "Unsupported file type: ${backup_file}"
  echo "Expected .sql or .sql.gz"
  exit 1
fi

if [[ "${auto_yes}" != "--yes" ]]; then
  cat <<EOF
WARNING: This will REPLACE current PostgreSQL data in schema public.
Backup file: ${backup_file}

Type RESTORE to continue:
EOF
  read -r confirmation
  if [[ "${confirmation}" != "RESTORE" ]]; then
    echo "Aborted."
    exit 1
  fi
fi

echo "Creating safety backup before restore..."
bash scripts/backup_postgres.sh

echo "Dropping and recreating public schema..."
docker compose exec -T db sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"'

echo "Restoring from ${backup_file}..."
if [[ "${backup_file}" == *.sql.gz ]]; then
  gzip -dc "${backup_file}" | docker compose exec -T db sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
else
  cat "${backup_file}" | docker compose exec -T db sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
fi

echo "Restore completed successfully."
