import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError

from app.config import load_settings
from app.db import close_pool, init_pool
from app.handlers import admin, user
from app.repository import Repository


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    pool = await init_pool(settings.database_url)
    repo = Repository(pool)
    dp = Dispatcher()
    dp["repo"] = repo

    dp.include_router(admin.router)
    dp.include_router(user.router)

    try:
        while True:
            session = AiohttpSession(
                proxy=settings.telegram_proxy,
                timeout=settings.telegram_request_timeout,
            )
            bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)

            try:
                await dp.start_polling(bot)
                break
            except (TelegramNetworkError, asyncio.TimeoutError, aiohttp.ClientError) as exc:
                logging.warning(
                    "Telegram API unreachable (%s). Retrying in %s seconds...",
                    exc,
                    settings.telegram_retry_delay,
                )
                await asyncio.sleep(settings.telegram_retry_delay)
            finally:
                await bot.session.close()
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
