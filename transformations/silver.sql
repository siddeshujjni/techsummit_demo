-- Meridian Customer 360 — Silver Layer
-- Denormalized facts from raw parquet (no bronze pass-through).
-- Raw data lives in /Volumes/techsummit_27/meridian_bank/raw_data/<dataset>

USE SCHEMA meridian_bank;

-- ─────────────────────────────────────────────────────────────────────────────
-- note_churn_flags: ai_classify showcase — one LLM call per DISTINCT note string
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW note_churn_flags
COMMENT 'Dedup ai_classify over distinct servicing notes — churn signal score per phrase'
AS
SELECT
  servicing_note_text,
  CASE ai_classify(servicing_note_text, ARRAY('churn_signal', 'at_risk', 'healthy'))
    WHEN 'churn_signal' THEN 1.0
    WHEN 'at_risk'      THEN 0.6
    ELSE 0.1
  END AS churn_signal_score
FROM (
  SELECT DISTINCT servicing_note_text
  FROM read_files('/Volumes/techsummit_27/meridian_bank/raw_data/risk_snapshots')
  WHERE servicing_note_text IS NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- silver_holdings: per customer×account denormalized fact
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW silver_holdings
COMMENT 'Customer holdings denormalized with customer dims and product details'
CLUSTER BY (customer_id)
AS
SELECT
  c.customer_id,
  c.customer_display_name,
  c.tier,
  c.tenure_years,
  c.home_metro,
  c.customer_lat,
  c.customer_lng,
  h.account_id,
  h.product_id,
  p.product_name,
  p.product_type,
  p.segment,
  h.balance_usd,
  h.maturity_date,
  h.rate_apy,
  h.status,
  CASE
    WHEN h.maturity_date IS NOT NULL THEN datediff(h.maturity_date, current_date() - 1)
    ELSE NULL
  END AS days_to_maturity
FROM read_files('/Volumes/techsummit_27/meridian_bank/raw_data/holdings') h
JOIN read_files('/Volumes/techsummit_27/meridian_bank/raw_data/customers') c
  ON h.customer_id = c.customer_id
JOIN read_files('/Volumes/techsummit_27/meridian_bank/raw_data/products') p
  ON h.product_id = p.product_id;

-- ─────────────────────────────────────────────────────────────────────────────
-- silver_risk: current + recent risk position, denormalized
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW silver_risk
COMMENT 'Risk snapshots denormalized with customer dims and ai_classify churn signal'
CLUSTER BY (snapshot_date)
AS
SELECT
  c.customer_id,
  c.customer_display_name,
  c.tier,
  c.tenure_years,
  c.home_metro,
  c.customer_lat,
  c.customer_lng,
  r.snapshot_date,
  r.attrition_risk_score,
  r.balance_outflow_30d_usd,
  r.servicing_note_text,
  COALESCE(n.churn_signal_score, 0.1) AS churn_signal_score
FROM read_files('/Volumes/techsummit_27/meridian_bank/raw_data/risk_snapshots') r
JOIN read_files('/Volumes/techsummit_27/meridian_bank/raw_data/customers') c
  ON r.customer_id = c.customer_id
LEFT JOIN note_churn_flags n
  ON r.servicing_note_text = n.servicing_note_text;

-- ─────────────────────────────────────────────────────────────────────────────
-- silver_campaigns: retention-action history, denormalized
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW silver_campaigns
COMMENT 'Historical retention campaigns denormalized with customer and product details'
AS
SELECT
  rc.campaign_id,
  rc.customer_id,
  c.tier,
  c.tenure_years,
  rc.product_id,
  p.product_name,
  rc.action_type,
  rc.offered_product_id,
  rc.balance_at_risk_usd,
  rc.attrition_risk_at_action,
  rc.initiated_date,
  rc.days_to_resolve,
  rc.retained,
  rc.retained_revenue_usd,
  rc.margin_impact_usd,
  rc.cost_usd
FROM read_files('/Volumes/techsummit_27/meridian_bank/raw_data/retention_campaigns') rc
JOIN read_files('/Volumes/techsummit_27/meridian_bank/raw_data/customers') c
  ON rc.customer_id = c.customer_id
JOIN read_files('/Volumes/techsummit_27/meridian_bank/raw_data/products') p
  ON rc.product_id = p.product_id;
