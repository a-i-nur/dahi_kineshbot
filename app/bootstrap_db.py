import asyncio
import os
from pathlib import Path

import asyncpg


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_DIR = ROOT_DIR / "db"
SCHEMA_FILE = DB_DIR / "schema.sql"
SEED_FILE = DB_DIR / "seed.sql"
MIGRATIONS_DIR = DB_DIR / "migrations"


def _parse_admin_usernames(raw: str) -> list[str]:
    usernames: list[str] = []
    for item in raw.split(","):
        username = item.strip()
        if not username:
            continue
        if not username.startswith("@"):
            username = f"@{username}"
        usernames.append(username)
    return usernames


async def _wait_for_db(database_url: str) -> asyncpg.Connection:
    last_error: Exception | None = None
    for _ in range(60):
        try:
            return await asyncpg.connect(database_url)
        except Exception as exc:  # pragma: no cover - startup retry path
            last_error = exc
            await asyncio.sleep(1)

    if last_error is not None:
        raise last_error
    raise RuntimeError("Unable to connect to database")


async def _apply_sql_file(conn: asyncpg.Connection, file_path: Path) -> None:
    sql = file_path.read_text(encoding="utf-8")
    await conn.execute(sql)


async def main() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    conn = await _wait_for_db(database_url)
    try:
        await _apply_sql_file(conn, SCHEMA_FILE)

        if MIGRATIONS_DIR.exists():
            for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
                await _apply_sql_file(conn, migration)

        await _apply_sql_file(conn, SEED_FILE)

        admin_usernames_raw = os.getenv("ADMIN_USERNAMES", "").strip()
        if admin_usernames_raw:
            for username in _parse_admin_usernames(admin_usernames_raw):
                await conn.execute(
                    """
                    INSERT INTO telegram_admins (tg_username, is_active)
                    VALUES ($1, TRUE)
                    ON CONFLICT (tg_username)
                    DO UPDATE SET is_active = EXCLUDED.is_active
                    """,
                    username,
                )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
