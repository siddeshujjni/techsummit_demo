-- Migration 001: Add retention scoring columns to rm_actions
-- Author: AI Coding Agent
-- Date: 2025-08-27
-- Branch: agent-migration-001
-- Ticket: Requirement — track predicted retention probability and model version

ALTER TABLE meridian_bank.rm_actions
ADD COLUMN IF NOT EXISTS retention_probability DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS model_version TEXT DEFAULT 'v1.0',
ADD COLUMN IF NOT EXISTS scored_at TIMESTAMPTZ DEFAULT now();

COMMENT ON COLUMN meridian_bank.rm_actions.retention_probability IS
    'ML model predicted probability of customer retention (0.0-1.0)';
COMMENT ON COLUMN meridian_bank.rm_actions.model_version IS
    'Version of the retention scoring model that generated this prediction';
COMMENT ON COLUMN meridian_bank.rm_actions.scored_at IS
    'Timestamp when the retention score was computed';

CREATE INDEX IF NOT EXISTS idx_rm_actions_retention_score
ON meridian_bank.rm_actions (retention_probability DESC NULLS LAST);
