from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.keyboards.user import main_reply_keyboard, quote_actions_keyboard, start_inline_keyboard
from app.repository import Repository
from app.utils.formatters import format_resources

router = Router()


async def _build_actions_keyboard(repo: Repository, author_id: int):
    has_audio = await repo.has_resources(author_id, "audio")
    has_materials = await repo.has_resources(author_id, "materials")
    return quote_actions_keyboard(author_id, has_audio=has_audio, has_materials=has_materials)


async def _send_random_quote(target: Message | CallbackQuery, repo: Repository) -> None:
    quote = await repo.get_random_quote()
    if isinstance(target, Message):
        message = target
    else:
        maybe_message = target.message
        if not isinstance(maybe_message, Message):
            return
        message = maybe_message

    if quote is None:
        text = "Цитаты пока не загружены в БД."
        await message.answer(text)
        return

    file_path = Path(quote.file_path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    if not file_path.exists():
        missing = f"Файл не найден: {quote.file_path}"
        await message.answer(missing)
        return

    caption = f"Цитата #{quote.image_number}\nАвтор: {quote.author_name}"
    keyboard = await _build_actions_keyboard(repo, quote.author_id)

    await message.answer_photo(photo=FSInputFile(str(file_path)), caption=caption)
    await message.answer("Сайлагыз:", reply_markup=keyboard)


@router.message(F.text == "/start")
async def start_handler(message: Message) -> None:
    await message.answer(
        "Сәлам! Биредә үзеңә көндәләк киңәш алу һәм даһи язучыларыбыз белән якынрак танышу мөмкинлеге бар.",
        reply_markup=main_reply_keyboard(),
    )
    await message.answer(
        "Очраклы киңәшне алыр өчен, төймәгә бас ⬇️",
        reply_markup=start_inline_keyboard(),
    )


@router.message(F.text.in_({"Получить цитату / Киңәш кирәк", "Получить цитату"}))
async def quote_handler(message: Message, repo: Repository) -> None:
    await _send_random_quote(message, repo)


@router.message(F.text == "Киңәш кирәк")
async def quote_tatar_handler(message: Message, repo: Repository) -> None:
    await _send_random_quote(message, repo)


@router.callback_query(F.data == "quote:next")
async def quote_next_handler(callback: CallbackQuery, repo: Repository) -> None:
    await callback.answer()
    await _send_random_quote(callback, repo)


@router.callback_query(F.data.regexp(r"^author:(bio|books|audio|materials):\d+$"))
async def author_actions_handler(callback: CallbackQuery, repo: Repository) -> None:
    await callback.answer()
    message = callback.message
    if not isinstance(message, Message):
        return

    data = callback.data
    if not data:
        await message.answer("Некорректный запрос.")
        return

    parts = data.split(":")
    if len(parts) != 3:
        await message.answer("Некорректный формат запроса.")
        return

    action, author_id_str = parts[1:]
    author_id = int(author_id_str)

    author = await repo.get_author(author_id)
    if author is None:
        await message.answer("Автор не найден в БД.")
        return

    if action == "bio":
        source_line = author.source_label
        if author.source_url:
            source_line = f"{author.source_label}: {author.source_url}"
        keyboard = await _build_actions_keyboard(repo, author_id)
        await message.answer(
            f"{author.display_name}\n\n{author.bio_full}\n\n{source_line}",
            reply_markup=keyboard,
        )
        return

    if action == "books":
        items = await repo.get_resources(author_id, "books")
        keyboard = await _build_actions_keyboard(repo, author_id)
        await message.answer(
            format_resources(items, "📘"),
            reply_markup=keyboard,
        )
        return

    if action == "audio":
        items = await repo.get_resources(author_id, "audio")
        keyboard = await _build_actions_keyboard(repo, author_id)
        await message.answer(
            format_resources(items, "🎧"),
            reply_markup=keyboard,
        )
        return

    if action == "materials":
        items = await repo.get_resources(author_id, "materials")
        keyboard = await _build_actions_keyboard(repo, author_id)
        await message.answer(
            format_resources(items, "📎"),
            reply_markup=keyboard,
        )
