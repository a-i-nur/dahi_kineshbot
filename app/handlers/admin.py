from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.keyboards.admin import yes_no_keyboard
from app.repository import Repository

router = Router()


class AddQuoteStates(StatesGroup):
    waiting_photo = State()
    waiting_number = State()
    waiting_author_name = State()
    waiting_create_author_confirm = State()
    waiting_bio_short = State()
    waiting_bio_full = State()
    waiting_source_url = State()
    waiting_books = State()
    waiting_audio = State()
    waiting_materials = State()
    waiting_save_confirm = State()


def _normalized_username(username: str | None) -> str:
    if not username:
        return ""
    return username if username.startswith("@") else f"@{username}"


async def _is_admin_user(message_or_callback: Message | CallbackQuery, repo: Repository) -> bool:
    user = message_or_callback.from_user
    if user is None:
        return False
    return await repo.is_admin_username(_normalized_username(user.username))


def _parse_resource_lines(raw_text: str) -> list[tuple[str, str | None]]:
    text = raw_text.strip()
    if text in {"-", "нет", "пропустить"}:
        return []

    items: list[tuple[str, str | None]] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if "|" in clean:
            title, url = clean.split("|", 1)
            items.append((title.strip(), url.strip() or None))
        else:
            items.append((clean, None))
    return items


async def _save_quote_card(bot: Bot, repo: Repository, data: dict) -> None:
    image_number = int(data["image_number"])
    author_id = int(data["author_id"])
    file_id = data["photo_file_id"]

    pics_dir = Path.cwd() / "pics"
    pics_dir.mkdir(parents=True, exist_ok=True)

    dst = pics_dir / f"{image_number}.png"
    tg_file = await bot.get_file(file_id)
    if not tg_file.file_path:
        raise RuntimeError("Telegram file path is empty")
    await bot.download_file(tg_file.file_path, destination=dst)

    await repo.upsert_quote_image(image_number=image_number, file_path=f"pics/{image_number}.png", author_id=author_id)


@router.message(F.text == "/admin")
async def admin_entry(message: Message, repo: Repository) -> None:
    if not await _is_admin_user(message, repo):
        await message.answer("Доступ запрещен.")
        return

    await message.answer(
        "Админ-режим:\n"
        "- /admin_add_quote — добавить новую карточку\n"
        "Ввод ссылок: одна строка = `Название | URL`.\n"
        "Чтобы пропустить блок, отправьте `-`."
    )


@router.message(F.text == "/admin_add_quote")
async def admin_add_quote_start(message: Message, state: FSMContext, repo: Repository) -> None:
    if not await _is_admin_user(message, repo):
        await message.answer("Доступ запрещен.")
        return

    await state.clear()
    await state.set_state(AddQuoteStates.waiting_photo)
    await message.answer("Шаг 1/7: отправьте PNG-картинку.")


@router.message(AddQuoteStates.waiting_photo)
async def admin_photo_step(message: Message, state: FSMContext) -> None:
    if not message.photo:
        await message.answer("Нужна картинка. Отправьте изображение как фото.")
        return

    largest = message.photo[-1]
    await state.update_data(photo_file_id=largest.file_id)
    await state.set_state(AddQuoteStates.waiting_number)
    await message.answer("Шаг 2/7: укажите номер картинки или `auto`.")


@router.message(AddQuoteStates.waiting_number)
async def admin_number_step(message: Message, state: FSMContext, repo: Repository) -> None:
    value = (message.text or "").strip().lower()
    if value == "auto":
        image_number = await repo.get_next_image_number()
    elif value.isdigit() and int(value) > 0:
        image_number = int(value)
    else:
        await message.answer("Введите положительное число или `auto`.")
        return

    await state.update_data(image_number=image_number)
    await state.set_state(AddQuoteStates.waiting_author_name)
    await message.answer("Шаг 3/7: введите имя автора.")


@router.message(AddQuoteStates.waiting_author_name)
async def admin_author_name_step(message: Message, state: FSMContext, repo: Repository) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Имя автора не должно быть пустым.")
        return

    author = await repo.get_author_by_name(name)
    await state.update_data(author_name=name)

    if author:
        await state.update_data(author_id=author.id)
        await state.set_state(AddQuoteStates.waiting_save_confirm)
        await message.answer(
            f"Автор найден: {author.display_name}. Сохранить карточку?",
            reply_markup=yes_no_keyboard("admin_save_quote"),
        )
        return

    await state.set_state(AddQuoteStates.waiting_create_author_confirm)
    await message.answer(
        "Автор не найден в БД. Создать нового автора?",
        reply_markup=yes_no_keyboard("admin_create_author"),
    )


@router.callback_query(
    AddQuoteStates.waiting_create_author_confirm,
    F.data.in_({"admin_create_author:yes", "admin_create_author:no"}),
)
async def admin_create_author_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    message = callback.message
    if not isinstance(message, Message):
        return

    data = callback.data
    if not data:
        await message.answer("Некорректный запрос.")
        return

    if data.endswith(":no"):
        await state.clear()
        await message.answer("Операция отменена.")
        return

    await state.set_state(AddQuoteStates.waiting_bio_short)
    await message.answer("Шаг 4/7: отправьте `bio_short`.")


@router.message(AddQuoteStates.waiting_bio_short)
async def admin_bio_short_step(message: Message, state: FSMContext) -> None:
    bio_short = (message.text or "").strip()
    if not bio_short:
        await message.answer("`bio_short` не должен быть пустым.")
        return

    await state.update_data(bio_short=bio_short)
    await state.set_state(AddQuoteStates.waiting_bio_full)
    await message.answer("Шаг 5/7: отправьте `bio_full` (полная биография).")


@router.message(AddQuoteStates.waiting_bio_full)
async def admin_bio_full_step(message: Message, state: FSMContext) -> None:
    bio_full = (message.text or "").strip()
    if not bio_full:
        await message.answer("`bio_full` не должен быть пустым.")
        return

    await state.update_data(bio_full=bio_full)
    await state.set_state(AddQuoteStates.waiting_source_url)
    await message.answer("Укажите ссылку `Чыганак` (или `-`, если нет).")


@router.message(AddQuoteStates.waiting_source_url)
async def admin_source_url_step(message: Message, state: FSMContext) -> None:
    source_url_raw = (message.text or "").strip()
    source_url = None if source_url_raw in {"", "-"} else source_url_raw
    await state.update_data(source_url=source_url)

    await state.set_state(AddQuoteStates.waiting_books)
    await message.answer(
        "Шаг 7/7: книги (по строкам `Название | URL`).\n"
        "Если нет данных, отправьте `-`."
    )


@router.message(AddQuoteStates.waiting_books)
async def admin_books_step(message: Message, state: FSMContext) -> None:
    await state.update_data(books=_parse_resource_lines(message.text or ""))
    await state.set_state(AddQuoteStates.waiting_audio)
    await message.answer("Аудио (по строкам `Название | URL`) или `-`.")


@router.message(AddQuoteStates.waiting_audio)
async def admin_audio_step(message: Message, state: FSMContext) -> None:
    await state.update_data(audio=_parse_resource_lines(message.text or ""))
    await state.set_state(AddQuoteStates.waiting_materials)
    await message.answer("Доп. материалы (по строкам `Название | URL`) или `-`.")


@router.message(AddQuoteStates.waiting_materials)
async def admin_materials_step(message: Message, state: FSMContext) -> None:
    await state.update_data(materials=_parse_resource_lines(message.text or ""))

    data = await state.get_data()
    summary = (
        "Проверьте данные:\n"
        f"- Номер картинки: {data['image_number']}\n"
        f"- Автор: {data['author_name']}\n"
        f"- Книг: {len(data.get('books', []))}\n"
        f"- Аудио: {len(data.get('audio', []))}\n"
        f"- Материалов: {len(data.get('materials', []))}\n"
        "Сохранить?"
    )
    await state.set_state(AddQuoteStates.waiting_save_confirm)
    await message.answer(summary, reply_markup=yes_no_keyboard("admin_save_quote"))


@router.callback_query(AddQuoteStates.waiting_save_confirm, F.data.in_({"admin_save_quote:yes", "admin_save_quote:no"}))
async def admin_save_confirm(callback: CallbackQuery, state: FSMContext, repo: Repository, bot: Bot) -> None:
    await callback.answer()
    message = callback.message
    if not isinstance(message, Message):
        return

    data = callback.data
    if not data:
        await message.answer("Некорректный запрос.")
        return

    if data.endswith(":no"):
        await state.clear()
        await message.answer("Операция отменена.")
        return

    state_data = await state.get_data()

    author_id = state_data.get("author_id")
    if author_id is None:
        author_name = state_data["author_name"]
        bio_short = state_data["bio_short"]
        bio_full = state_data["bio_full"]

        source_url = state_data.get("source_url")
        author_id = await repo.create_author(
            author_name,
            bio_short=bio_short,
            bio_full=bio_full,
            source_label="Чыганак",
            source_url=source_url,
        )
        await repo.add_resources(author_id, "books", state_data.get("books", []))
        await repo.add_resources(author_id, "audio", state_data.get("audio", []))
        await repo.add_resources(author_id, "materials", state_data.get("materials", []))

    await state.update_data(author_id=author_id)

    await _save_quote_card(bot, repo, await state.get_data())
    await state.clear()

    await message.answer("Карточка и данные автора успешно сохранены.")
