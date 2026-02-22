from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Киңәш кирәк")]],
        resize_keyboard=True,
    )


def start_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Киңәш кирәк", callback_data="quote:next")]
        ]
    )


def quote_actions_keyboard(author_id: int, has_audio: bool, has_materials: bool) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="Язучы турында", callback_data=f"author:bio:{author_id}")],
        [InlineKeyboardButton(text="Әсәрләрен укырга", callback_data=f"author:books:{author_id}")],
    ]

    if has_audio:
        buttons.append([InlineKeyboardButton(text="Аудиокитаплар тыңларга", callback_data=f"author:audio:{author_id}")])
    if has_materials:
        buttons.append([InlineKeyboardButton(text="Өстәмә мәгълүмат", callback_data=f"author:materials:{author_id}")])

    buttons.append([InlineKeyboardButton(text="Тагын бер киңәш", callback_data="quote:next")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
