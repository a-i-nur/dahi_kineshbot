from app.repository import ResourceItem


def format_resources(items: list[ResourceItem], emoji: str) -> str:
    if not items:
        return "Пока нет данных."

    lines: list[str] = []
    for item in items:
        if item.url:
            lines.append(f"{emoji} {item.title} — {item.url}")
        else:
            lines.append(f"{emoji} {item.title}")
    return "\n".join(lines)
