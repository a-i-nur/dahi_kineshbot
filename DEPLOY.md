# Deploy Checklist

Short, practical checklist for the current production setup.

## First server setup

1. Log in as `root` on the fresh VPS.
2. Update the system:
   ```bash
   apt update && apt -y upgrade
   ```
3. Create the `deploy` user and add it to sudo:
   ```bash
   adduser deploy
   usermod -aG sudo deploy
   ```
4. Add your SSH public key to `/home/deploy/.ssh/authorized_keys`.
5. Reconnect as `deploy` and verify SSH key login works.
6. Disable root and password SSH login after key access is confirmed.
7. Install Docker + Compose plugin.
8. Add `deploy` to the `docker` group and reconnect once more.
9. Clone the repo into `/opt/dahi_kineshbot`.
10. Create `.env` from `.env.example` and fill in the real values.

## Production deploy

1. Pull the latest repo changes:
   ```bash
   git pull
   ```
2. Pull the Docker image:
   ```bash
   docker compose pull
   ```
3. Start the stack:
   ```bash
   docker compose up -d
   ```
4. Watch logs:
   ```bash
   docker compose logs -f bot
   ```

## GitHub Actions deploy

This repository has a workflow in [.github/workflows/deploy.yml](.github/workflows/deploy.yml) that:

1. Builds the Docker image on every push to `master`.
2. Pushes the image to Docker Hub.
3. Connects to the VPS over SSH and runs `git pull && docker compose pull && docker compose up -d`.

Required GitHub Secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SSH_HOST`
- `SSH_USER`
- `SSH_KEY`

Notes:

- The server must already have the repo cloned in `/opt/dahi_kineshbot`.
- The server must have Docker and the Compose plugin installed.
- `SSH_KEY` should be the private key that matches the public key added to the server's `deploy` user.

## Quick checks

1. `docker compose ps`
2. `docker compose logs -f bot`
3. In Telegram, send `/start` and then `Киңәш кирәк`

## Minimal PostgreSQL backup

The simplest backup is a daily `pg_dump` from the host into a local `backups/` directory.

1. Create the backup directory on the server:
   ```bash
   mkdir -p backups
   ```
2. Run the backup script from the project root:
   ```bash
   bash scripts/backup_postgres.sh
   ```
3. The dump will be saved as a compressed file like `backups/dahi_kineshbot-20260421-020000.sql.gz`.
4. Keep at least several recent files and delete old ones manually or with `find`.

Suggested cron example:

```cron
0 2 * * * cd /opt/dahi_kineshbot && bash scripts/backup_postgres.sh >/tmp/dahi_backup.log 2>&1
```

## PostgreSQL restore

Use this only when you need to recover from a dump.

1. Pick a backup file from `backups/`.
2. Run restore from project root:
   ```bash
   bash scripts/restore_postgres.sh backups/dahi_kineshbot-YYYYMMDD-HHMMSS.sql.gz
   ```
3. Confirm by typing `RESTORE`.

Notes:

- The restore script creates a safety backup first.
- It then drops and recreates schema `public` and loads the dump.
- For non-interactive usage, pass `--yes` as the second argument.

## Notes

- `BOT_IMAGE` can override the default Docker Hub image tag.
- `TELEGRAM_PROXY` can stay empty on a stable EU server.
- `restart: unless-stopped` keeps the bot up after reboots.