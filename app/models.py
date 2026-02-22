from dataclasses import dataclass


@dataclass(slots=True)
class Author:
    id: int
    display_name: str
    bio_short: str
    bio_full: str
    source_label: str
    source_url: str | None


@dataclass(slots=True)
class QuoteCard:
    image_number: int
    file_path: str
    author_id: int
    author_name: str
    author_bio_short: str
