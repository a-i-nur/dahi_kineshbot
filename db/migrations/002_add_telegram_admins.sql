-- Add Telegram admin allow-list table
CREATE TABLE IF NOT EXISTS telegram_admins (
  id            BIGSERIAL PRIMARY KEY,
  tg_username   TEXT NOT NULL UNIQUE,
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT tg_username_format CHECK (tg_username ~ '^@[A-Za-z0-9_]{5,32}$')
);
