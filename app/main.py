import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
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

    session = AiohttpSession(timeout=aiohttp.ClientTimeout(total=60))
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)
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
