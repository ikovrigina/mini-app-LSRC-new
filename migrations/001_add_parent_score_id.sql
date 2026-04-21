-- Add parent_score_id to scores table for score lineage tracking
-- Run this in Supabase SQL Editor

ALTER TABLE scores ADD COLUMN IF NOT EXISTS parent_score_id UUID REFERENCES scores(id);

CREATE INDEX IF NOT EXISTS idx_scores_parent ON scores(parent_score_id);
