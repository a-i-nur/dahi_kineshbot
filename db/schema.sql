-- PostgreSQL schema for dahi_kineshbot

-- 1) Authors directory (bio and metadata)
CREATE TABLE IF NOT EXISTS authors (
  id            BIGSERIAL PRIMARY KEY,
  slug          TEXT NOT NULL UNIQUE,
  display_name  TEXT NOT NULL UNIQUE,
  bio_short     TEXT NOT NULL,
  bio_full      TEXT NOT NULL,
  source_label  TEXT NOT NULL DEFAULT 'Чыганак',
  source_url    TEXT,
  born_date     DATE,
  died_date     DATE,
  birth_place   TEXT,
  death_place   TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) Mapping image -> author
-- image_number is the business identifier from file name: pics/{image_number}.png
CREATE TABLE IF NOT EXISTS quote_images (
  id            BIGSERIAL PRIMARY KEY,
  image_number  INTEGER NOT NULL UNIQUE,
  file_path     TEXT NOT NULL UNIQUE,
  author_id     BIGINT NOT NULL REFERENCES authors(id) ON DELETE RESTRICT,
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT image_number_positive CHECK (image_number > 0)
);

-- Useful index for random selection and joins
CREATE INDEX IF NOT EXISTS idx_quote_images_author_id
  ON quote_images(author_id);

-- Optional: author resources (books/audio/materials)
CREATE TABLE IF NOT EXISTS author_resources (
  id            BIGSERIAL PRIMARY KEY,
  author_id     BIGINT NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
  resource_type TEXT NOT NULL,
  title         TEXT NOT NULL,
  url           TEXT,
  sort_order    INTEGER NOT NULL DEFAULT 100,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT resource_type_check CHECK (resource_type IN ('books', 'audio', 'materials'))
);

CREATE INDEX IF NOT EXISTS idx_author_resources_author_type
  ON author_resources(author_id, resource_type, sort_order);

-- Admin allow-list by Telegram username
CREATE TABLE IF NOT EXISTS telegram_admins (
  id            BIGSERIAL PRIMARY KEY,
  tg_username   TEXT NOT NULL UNIQUE,
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT tg_username_format CHECK (tg_username ~ '^@[A-Za-z0-9_]{5,32}$')
);
