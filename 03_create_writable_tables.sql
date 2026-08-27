-- Milestone 2.3 — Create writable rm_actions table
-- Run against: databricks_postgres on meridian-bank/production

CREATE TABLE meridian_bank.rm_actions (
    action_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    customer_id TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    recommended_offer_product_id TEXT,
    recommended_rate_apy NUMERIC(5,4),
    predicted_retained_usd DOUBLE PRECISION,
    approved_by TEXT NOT NULL,
    approved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'approved',
    notes TEXT
);
