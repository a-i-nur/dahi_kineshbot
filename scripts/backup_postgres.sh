#!/usr/bin/env bash

set -euo pipefail

backup_dir="backups"
timestamp="$(date +%Y%m%d-%H%M%S)"
backup_file="${backup_dir}/dahi_kineshbot-${timestamp}.sql.gz"

mkdir -p "${backup_dir}"

docker compose exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  | gzip > "${backup_file}"

echo "Backup saved to ${backup_file}"