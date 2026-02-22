import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    pics_dir: Path


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()
    pics_dir = Path(os.getenv("PICS_DIR", "pics")).resolve()

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return Settings(bot_token=bot_token, database_url=database_url, pics_dir=pics_dir)
