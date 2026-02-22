# dahi_kineshbot

Telegram bot that sends random quote cards (PNG) and lets users open author information (bio, books, audio, extra materials).

The bot is content-driven:
- quote images are read from `pics/*.png`
- metadata is read from PostgreSQL (`authors`, `quote_images`, `author_resources`)

## Features

- `/start` greeting
- main action button: `Киңәш кирәк`
- random quote image with author name
- inline action buttons (Tatar):
  - `Язучы турында`
  - `Әсәрләрен укырга`
  - `Аудиокитаплар тыңларга` (shown only if audio exists)
  - `Өстәмә мәгълүмат` (shown only if materials exist)
  - `Тагын бер киңәш`
- admin flow in Telegram (`/admin`, `/admin_add_quote`)
- admin access controlled by DB table `telegram_admins`

## How it works

1. User requests a quote (`Киңәш кирәк` or `Тагын бер киңәш`).
2. Bot selects one random active row from `quote_images`.
3. Bot sends `pics/{image_number}.png`.
4. Bot loads author from `authors` and resources from `author_resources`.
5. Bot renders action buttons based on available resources.

## Project structure

```text
app/
  handlers/
  keyboards/
  utils/
  config.py
  db.py
  repository.py
  main.py

db/
  schema.sql
  seed.sql
  migrations/

pics/
Dockerfile
docker-compose.yml
```

## Minimum environment

Required:
- Python 3.11+
- PostgreSQL 15+ (or Dockerized Postgres)
- Telegram bot token from BotFather

Optional but recommended:
- Docker 24+
- Docker Compose plugin (`docker compose`)

## Configuration

Use `.env` (never commit it):

```env
BOT_TOKEN=your_real_bot_token
DATABASE_URL=postgresql://user:password@localhost:5432/dahi_kineshbot

# Optional: comma-separated Telegram usernames to auto-whitelist as admins on container start
# Example: ADMIN_USERNAMES=@alice,@bob
ADMIN_USERNAMES=

# Optional (for docker-compose defaults)
POSTGRES_DB=dahi_kineshbot
POSTGRES_USER=dahi
POSTGRES_PASSWORD=dahi_password
```

Templates:
- `.env.example`
- `.env.docker.example`

## Local run (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/migrations/001_add_bio_full.sql
psql "$DATABASE_URL" -f db/migrations/002_add_telegram_admins.sql
psql "$DATABASE_URL" -f db/migrations/003_author_source_and_remove_bio_short_limit.sql
psql "$DATABASE_URL" -f db/seed.sql

python -m app.main
```

## Docker run

```bash
docker compose up --build -d
docker compose logs -f bot
```

Stop:

```bash
docker compose down
```

The container entrypoint automatically applies:
- `db/schema.sql`
- all `db/migrations/*.sql`
- `db/seed.sql`
- optional admin bootstrap from `ADMIN_USERNAMES`

## Deploy to a server (VPS)

Recommended path:
1. Provision Ubuntu VPS.
2. Install Docker + Compose plugin.
3. Copy project to server.
4. Create `.env` with real token and DB settings.
5. Run `docker compose up --build -d`.
6. Check `docker compose logs -f bot`.

Because `restart: unless-stopped` is enabled, services auto-restart after reboot.

## How to find and test the bot in Telegram

1. Open Telegram.
2. Find the bot by username (current deployment example: `@dahi_kineshbot`).
3. Send `/start`.
4. Press `Киңәш кирәк`.
5. Verify quote card + action buttons.

## Admin panel behavior

Commands:
- `/admin` — help
- `/admin_add_quote` — step-by-step content upload

Flow for `/admin_add_quote`:
1. Send PNG image.
2. Send image number or `auto`.
3. Send author name.
4. If author exists, continue.
5. If author does not exist, bot asks for:
   - `bio_short`
   - `bio_full`
   - `Чыганак` URL
   - books/audio/materials
6. Bot saves image + DB records.

Access control:
- allowed only for usernames present in `telegram_admins` with `is_active = TRUE`

## Security checklist (what not to commit)

Do NOT commit:
- `.env` and any secret env files
- bot token
- private admin usernames list (store in `ADMIN_USERNAMES` or private SQL)
- private keys/certs (`*.pem`, `*.key`)
- local dumps/logs with sensitive data

If token was ever exposed, rotate it in BotFather immediately.

## SQL quick checks

Check admins:

```sql
SELECT tg_username, is_active
FROM telegram_admins
ORDER BY tg_username;
```

Add/update admin manually:

```sql
INSERT INTO telegram_admins (tg_username, is_active)
VALUES ('@new_admin', TRUE)
ON CONFLICT (tg_username) DO UPDATE SET is_active = EXCLUDED.is_active;
```
