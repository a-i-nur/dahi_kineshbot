import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    pics_dir: Path
    telegram_proxy: str | None
    telegram_request_timeout: int
    telegram_retry_delay: int


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be > 0")
    return value


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()
    pics_dir = Path(os.getenv("PICS_DIR", "pics")).resolve()
    telegram_proxy = os.getenv("TELEGRAM_PROXY", "").strip() or None
    telegram_request_timeout = _get_int_env("TELEGRAM_REQUEST_TIMEOUT", 120)
    telegram_retry_delay = _get_int_env("TELEGRAM_RETRY_DELAY", 15)

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return Settings(
        bot_token=bot_token,
        database_url=database_url,
        pics_dir=pics_dir,
        telegram_proxy=telegram_proxy,
        telegram_request_timeout=telegram_request_timeout,
        telegram_retry_delay=telegram_retry_delay,
    )
