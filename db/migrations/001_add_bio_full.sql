-- Add full biography field to existing authors table
ALTER TABLE authors
ADD COLUMN IF NOT EXISTS bio_full TEXT;

-- Ensure old rows are backfilled before NOT NULL constraint
UPDATE authors
SET bio_full = COALESCE(NULLIF(trim(bio_full), ''), bio_short)
WHERE bio_full IS NULL OR trim(bio_full) = '';

ALTER TABLE authors
ALTER COLUMN bio_full SET NOT NULL;
