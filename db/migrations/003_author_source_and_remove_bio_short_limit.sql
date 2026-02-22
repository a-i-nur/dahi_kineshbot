-- Add source fields and remove old short bio length limit
ALTER TABLE authors
ADD COLUMN IF NOT EXISTS source_label TEXT,
ADD COLUMN IF NOT EXISTS source_url TEXT;

UPDATE authors
SET source_label = COALESCE(NULLIF(trim(source_label), ''), 'Чыганак');

ALTER TABLE authors
ALTER COLUMN source_label SET NOT NULL,
ALTER COLUMN source_label SET DEFAULT 'Чыганак';

ALTER TABLE authors
DROP CONSTRAINT IF EXISTS bio_short_len;
