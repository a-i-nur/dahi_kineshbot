import hashlib
import re
from dataclasses import dataclass
from typing import Iterable

import asyncpg

from app.models import Author, QuoteCard

SPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class ResourceItem:
    title: str
    url: str | None


class Repository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def get_random_quote(self) -> QuoteCard | None:
        query = """
        SELECT
          qi.image_number,
          qi.file_path,
          a.id AS author_id,
          a.display_name AS author_name,
          a.bio_short AS author_bio_short
        FROM quote_images qi
        JOIN authors a ON a.id = qi.author_id
        WHERE qi.is_active = TRUE
        ORDER BY random()
        LIMIT 1
        """
        row = await self.pool.fetchrow(query)
        if not row:
            return None

        return QuoteCard(
            image_number=row["image_number"],
            file_path=row["file_path"],
            author_id=row["author_id"],
            author_name=row["author_name"],
            author_bio_short=row["author_bio_short"],
        )

    async def get_author(self, author_id: int) -> Author | None:
        row = await self.pool.fetchrow(
            """
            SELECT id, display_name, bio_short, bio_full, source_label, source_url
            FROM authors
            WHERE id = $1
            """,
            author_id,
        )
        if not row:
            return None
        return Author(
            id=row["id"],
            display_name=row["display_name"],
            bio_short=row["bio_short"],
            bio_full=row["bio_full"],
            source_label=row["source_label"],
            source_url=row["source_url"],
        )

    async def get_author_by_name(self, name: str) -> Author | None:
        row = await self.pool.fetchrow(
            """
            SELECT id, display_name, bio_short, bio_full, source_label, source_url
            FROM authors
            WHERE lower(display_name) = lower($1)
            LIMIT 1
            """,
            name.strip(),
        )
        if not row:
            return None
        return Author(
            id=row["id"],
            display_name=row["display_name"],
            bio_short=row["bio_short"],
            bio_full=row["bio_full"],
            source_label=row["source_label"],
            source_url=row["source_url"],
        )

    async def get_resources(self, author_id: int, resource_type: str) -> list[ResourceItem]:
        rows = await self.pool.fetch(
            """
            SELECT title, url
            FROM author_resources
            WHERE author_id = $1 AND resource_type = $2
            ORDER BY sort_order, id
            """,
            author_id,
            resource_type,
        )
        return [ResourceItem(title=row["title"], url=row["url"]) for row in rows]

    async def has_resources(self, author_id: int, resource_type: str) -> bool:
        value = await self.pool.fetchval(
            """
            SELECT EXISTS(
              SELECT 1
              FROM author_resources
              WHERE author_id = $1 AND resource_type = $2
            )
            """,
            author_id,
            resource_type,
        )
        return bool(value)

    async def is_admin_username(self, username: str | None) -> bool:
        if not username:
            return False
        normalized = username if username.startswith("@") else f"@{username}"
        value = await self.pool.fetchval(
            """
            SELECT EXISTS(
              SELECT 1
              FROM telegram_admins
              WHERE tg_username = $1 AND is_active = TRUE
            )
            """,
            normalized,
        )
        return bool(value)

    async def get_next_image_number(self) -> int:
        value = await self.pool.fetchval("SELECT COALESCE(MAX(image_number), 0) + 1 FROM quote_images")
        return int(value)

    async def create_author(
        self,
        display_name: str,
        bio_short: str,
        bio_full: str,
        source_label: str = "Чыганак",
        source_url: str | None = None,
    ) -> int:
        slug = self._slugify(display_name)
        row = await self.pool.fetchrow(
            """
            INSERT INTO authors (slug, display_name, bio_short, bio_full, source_label, source_url)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (slug) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                bio_short = EXCLUDED.bio_short,
                bio_full = EXCLUDED.bio_full,
                source_label = EXCLUDED.source_label,
                source_url = EXCLUDED.source_url,
                updated_at = NOW()
            RETURNING id
            """,
            slug,
            display_name.strip(),
            bio_short.strip(),
            bio_full.strip(),
            source_label.strip() or "Чыганак",
            (source_url or "").strip() or None,
        )
        return int(row["id"])

    async def upsert_quote_image(self, image_number: int, file_path: str, author_id: int) -> None:
        await self.pool.execute(
            """
            INSERT INTO quote_images (image_number, file_path, author_id, is_active)
            VALUES ($1, $2, $3, TRUE)
            ON CONFLICT (image_number) DO UPDATE
            SET file_path = EXCLUDED.file_path,
                author_id = EXCLUDED.author_id,
                is_active = TRUE
            """,
            image_number,
            file_path,
            author_id,
        )

    async def add_resources(
        self,
        author_id: int,
        resource_type: str,
        items: Iterable[tuple[str, str | None]],
    ) -> None:
        for idx, (title, url) in enumerate(items, start=1):
            clean_title = title.strip()
            clean_url = (url or "").strip() or None
            if not clean_title:
                continue
            await self.pool.execute(
                """
                INSERT INTO author_resources (author_id, resource_type, title, url, sort_order)
                VALUES ($1, $2, $3, $4, $5)
                """,
                author_id,
                resource_type,
                clean_title,
                clean_url,
                idx * 10,
            )

    @staticmethod
    def _slugify(value: str) -> str:
        base = value.lower().strip()
        normalized = SPACE_RE.sub("-", base)
        if not normalized:
            normalized = "author"
        suffix = hashlib.sha1(base.encode("utf-8")).hexdigest()[:8]
        return f"{normalized}-{suffix}"
