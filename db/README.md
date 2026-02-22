# DB design for dahi_kineshbot

## Почему так

Минимальный устойчивый слой данных:

- `authors` — карточка автора (био и метаданные)
- `quote_images` — связь `номер картинки -> автор`
- `author_resources` — книги/аудио/доп. материалы
- `telegram_admins` — allow-list админов по Telegram логину

Это позволяет:

1. Не держать логику в коде.
2. Масштабироваться с 40 до N карточек без изменения backend-кода.
3. Добавлять авторов и материалы через SQL/админку.

В `authors` теперь:

- `bio_short` — краткий текст (без жесткого ограничения 500 символов)
- `bio_full` — полный текст биографии
- `source_label` — подпись источника (обычно `Чыганак`)
- `source_url` — ссылка на источник

## Где хранить картинки

Рекомендуемый практичный вариант на старте:

- Файлы: `pics/{N}.png` на диске (или volume в Docker)
- В БД: только `image_number` и `file_path`

Почему не blob в БД:

- PNG удобнее отдавать с файловой системы/объектного хранилища.
- БД остаётся компактной и быстрее в бэкапах.

Для продакшена можно перейти на S3/MinIO и хранить в `file_path` URL.

## Как работает выдача случайной цитаты

```sql
SELECT
  qi.image_number,
  qi.file_path,
  a.id AS author_id,
  a.display_name,
  a.bio_full,
  a.source_label,
  a.source_url
FROM quote_images qi
JOIN authors a ON a.id = qi.author_id
WHERE qi.is_active = TRUE
ORDER BY random()
LIMIT 1;
```

После выбора автора можно подтянуть ресурсы:

```sql
SELECT resource_type, title, url
FROM author_resources
WHERE author_id = $1
ORDER BY resource_type, sort_order, id;
```

Проверка доступа к админ-командам:

```sql
SELECT 1
FROM telegram_admins
WHERE tg_username = $1
  AND is_active = TRUE;
```

## Инициализация

```bash
psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/seed.sql
```

Если БД уже была создана старой версией схемы:

```bash
psql "$DATABASE_URL" -f db/migrations/001_add_bio_full.sql
psql "$DATABASE_URL" -f db/migrations/002_add_telegram_admins.sql
psql "$DATABASE_URL" -f db/migrations/003_author_source_and_remove_bio_short_limit.sql
psql "$DATABASE_URL" -f db/seed.sql
```

## Важно

Текущая версия данных рассчитана на 6 авторов (по `autors_of_pics.md` и `data.pdf`).

В `seed.sql` загружены все 6 авторов.

Admin usernames are intentionally not stored in `db/seed.sql`.
Use runtime bootstrap via `ADMIN_USERNAMES` environment variable.
