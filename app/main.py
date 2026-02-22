import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import load_settings
from app.db import close_pool, init_pool
from app.handlers import admin, user
from app.repository import Repository


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    pool = await init_pool(settings.database_url)
    repo = Repository(pool)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp["repo"] = repo

    dp.include_router(admin.router)
    dp.include_router(user.router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
