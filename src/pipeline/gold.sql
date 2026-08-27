-- Meridian Customer 360 — Gold Layer
-- Aggregated customer position, at-risk view, campaign outcomes, and NBA heuristic.

USE SCHEMA meridian_bank;

-- ─────────────────────────────────────────────────────────────────────────────
-- gold_customer_position: one row per customer — CURRENT snapshot only
-- The heart of the demo: dashboard scatter/map, metric view, Genie, app all read this.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW gold_customer_position
COMMENT 'Per-customer current position: balances, risk, band flag. The coherence spine.'
CLUSTER BY (tier, risk_band)
AS
WITH holdings_agg AS (
  SELECT
    customer_id,
    COUNT(*) AS product_count,
    SUM(CASE WHEN status = 'active' THEN balance_usd ELSE 0 END) AS total_balance_usd,
    SUM(CASE WHEN status = 'active' AND segment = 'deposit' THEN balance_usd ELSE 0 END) AS deposit_balance_usd,
    SUM(CASE WHEN status = 'active' AND product_id IN ('PROD-DEP-2001', 'PROD-DEP-2002', 'PROD-DEP-2003') THEN balance_usd ELSE 0 END) AS affected_deposit_balance_usd,
    MIN(CASE WHEN product_id IN ('PROD-DEP-2001', 'PROD-DEP-2002', 'PROD-DEP-2003') AND days_to_maturity IS NOT NULL THEN days_to_maturity END) AS min_days_to_maturity
  FROM silver_holdings
  GROUP BY customer_id
),
current_risk AS (
  SELECT
    customer_id,
    customer_display_name,
    tier,
    tenure_years,
    home_metro,
    customer_lat,
    customer_lng,
    attrition_risk_score,
    balance_outflow_30d_usd,
    churn_signal_score
  FROM silver_risk
  WHERE snapshot_date = current_date() - 1
),
profile AS (
  SELECT customer_id, profile_summary
  FROM read_files('/Volumes/techsummit_27/meridian_bank/raw_data/customers')
)
SELECT
  r.customer_id,
  r.customer_display_name,
  r.tier,
  r.tenure_years,
  r.home_metro,
  r.customer_lat,
  r.customer_lng,
  prof.profile_summary,
  COALESCE(h.total_balance_usd, 0) AS total_balance_usd,
  COALESCE(h.deposit_balance_usd, 0) AS deposit_balance_usd,
  COALESCE(h.affected_deposit_balance_usd, 0) AS affected_deposit_balance_usd,
  h.min_days_to_maturity,
  r.attrition_risk_score,
  r.balance_outflow_30d_usd,
  r.churn_signal_score,
  COALESCE(h.product_count, 0) AS product_count,
  -- balance_at_risk: affected deposit balance when risk >= 0.6
  CASE WHEN r.attrition_risk_score >= 0.6 THEN COALESCE(h.affected_deposit_balance_usd, 0) ELSE 0 END AS balance_at_risk_usd,
  -- revenue_at_risk: balance * NIM + tenure fee value when at risk
  CASE WHEN r.attrition_risk_score >= 0.6
    THEN COALESCE(h.affected_deposit_balance_usd, 0) * 0.025 + GREATEST(0, r.tenure_years * 40)
    ELSE 0
  END AS revenue_at_risk_usd,
  -- risk_band: the single column the UI colors by
  CASE
    WHEN r.attrition_risk_score >= 0.75 AND COALESCE(h.affected_deposit_balance_usd, 0) > 0 THEN 'critical'
    WHEN r.attrition_risk_score >= 0.6 THEN 'elevated'
    WHEN r.attrition_risk_score >= 0.4 THEN 'watch'
    ELSE 'healthy'
  END AS risk_band
FROM current_risk r
LEFT JOIN holdings_agg h ON r.customer_id = h.customer_id
LEFT JOIN profile prof ON r.customer_id = prof.customer_id;

-- ─────────────────────────────────────────────────────────────────────────────
-- gold_open_atrisk: at-risk customers for the app + model scoring input
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW gold_open_atrisk
COMMENT 'Current at-risk customers with top affected holding and cross-sell candidate'
AS
WITH affected_holdings_ranked AS (
  SELECT
    customer_id,
    product_id AS atrisk_product_id,
    balance_usd AS atrisk_balance_usd,
    days_to_maturity,
    rate_apy AS current_rate_apy,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY balance_usd DESC) AS rn
  FROM silver_holdings
  WHERE product_id IN ('PROD-DEP-2001', 'PROD-DEP-2002', 'PROD-DEP-2003')
    AND status = 'active'
),
customer_segments AS (
  SELECT
    customer_id,
    MAX(CASE WHEN segment = 'investment' THEN 1 ELSE 0 END) AS has_investment,
    MAX(CASE WHEN segment = 'lending' THEN 1 ELSE 0 END) AS has_lending
  FROM silver_holdings
  WHERE status = 'active'
  GROUP BY customer_id
)
SELECT
  gcp.customer_id,
  gcp.customer_display_name,
  gcp.tier,
  gcp.tenure_years,
  gcp.home_metro,
  gcp.customer_lat,
  gcp.customer_lng,
  gcp.attrition_risk_score,
  gcp.balance_at_risk_usd,
  gcp.revenue_at_risk_usd,
  gcp.risk_band,
  ah.atrisk_product_id,
  ah.atrisk_balance_usd,
  ah.days_to_maturity,
  ah.current_rate_apy,
  0.0385 - COALESCE(ah.current_rate_apy, 0.0325) AS rate_gap,
  -- Candidate cross-sell: first segment they lack
  CASE
    WHEN COALESCE(cs.has_investment, 0) = 0 THEN 'PROD-INV-3001'
    WHEN COALESCE(cs.has_lending, 0) = 0 THEN 'PROD-CRD-4001'
    ELSE 'PROD-LN-5001'
  END AS candidate_cross_sell_product_id
FROM gold_customer_position gcp
LEFT JOIN affected_holdings_ranked ah
  ON gcp.customer_id = ah.customer_id AND ah.rn = 1
LEFT JOIN customer_segments cs
  ON gcp.customer_id = cs.customer_id
WHERE gcp.risk_band IN ('critical', 'elevated', 'watch');

-- ─────────────────────────────────────────────────────────────────────────────
-- gold_campaign_outcomes: training table for the NBA model
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW gold_campaign_outcomes
COMMENT 'Historical retention actions with outcomes — NBA model training table'
AS
SELECT
  campaign_id,
  customer_id,
  tier,
  tenure_years,
  action_type,
  balance_at_risk_usd,
  product_id,
  product_name,
  attrition_risk_at_action,
  offered_product_id,
  initiated_date,
  days_to_resolve,
  retained,
  retained_revenue_usd,
  margin_impact_usd,
  cost_usd
FROM silver_campaigns;

-- ─────────────────────────────────────────────────────────────────────────────
-- gold_nba_recommendations: ranked next-best-action per at-risk customer (HEURISTIC)
-- For each at-risk customer, score 3 candidate actions and pick the best by net value.
-- retention_offer wins for high-balance/high-risk (the hero); cross_sell wins for moderate.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REFRESH MATERIALIZED VIEW gold_nba_recommendations
COMMENT 'Ranked next-best-action per at-risk customer — heuristic scoring (no ML required)'
AS
WITH scored AS (
  SELECT
    customer_id,
    candidate_cross_sell_product_id,
    attrition_risk_score,
    current_rate_apy,
    -- Effective balance for scoring
    GREATEST(COALESCE(atrisk_balance_usd, 0), balance_at_risk_usd) AS eff_bal,

    -- retention_offer
    GREATEST(COALESCE(atrisk_balance_usd, 0), balance_at_risk_usd) * 0.025 * 3
      * LEAST(0.9, 0.45 + attrition_risk_score * 0.4) AS ret_retained,
    GREATEST(COALESCE(atrisk_balance_usd, 0), balance_at_risk_usd)
      * GREATEST(0.001, 0.0385 - COALESCE(current_rate_apy, 0.0325)) AS ret_cost,

    -- cross_sell
    GREATEST(COALESCE(atrisk_balance_usd, 0), balance_at_risk_usd) * 0.025 * 3
      * GREATEST(0.1, 0.6 - attrition_risk_score * 0.5) + 1200 AS xs_retained,

    -- rm_outreach
    GREATEST(COALESCE(atrisk_balance_usd, 0), balance_at_risk_usd) * 0.025 * 3
      * GREATEST(0.05, 0.4 - attrition_risk_score * 0.35) AS rm_retained
  FROM gold_open_atrisk
),
with_net AS (
  SELECT
    customer_id,
    candidate_cross_sell_product_id,
    attrition_risk_score,
    current_rate_apy,
    eff_bal,
    -- Net values (retained - cost - margin_impact)
    ret_retained - ret_cost AS ret_net,
    xs_retained - 50 AS xs_net,
    rm_retained - 40 AS rm_net,
    -- Raw retained
    ret_retained,
    ret_cost,
    xs_retained,
    rm_retained
  FROM scored
)
SELECT
  customer_id,
  -- recommended_action = argmax(net_value)
  CASE
    WHEN ret_net >= xs_net AND ret_net >= rm_net THEN 'retention_offer'
    WHEN xs_net >= ret_net AND xs_net >= rm_net THEN 'cross_sell'
    ELSE 'rm_outreach'
  END AS recommended_action,
  -- recommended_offer_product_id (cross-sell target for cross_sell, NULL otherwise)
  CASE
    WHEN xs_net >= ret_net AND xs_net >= rm_net THEN candidate_cross_sell_product_id
    ELSE NULL
  END AS recommended_offer_product_id,
  -- recommended_rate_apy (competitor rate for retention_offer, NULL otherwise)
  CASE
    WHEN ret_net >= xs_net AND ret_net >= rm_net THEN 0.0385
    ELSE NULL
  END AS recommended_rate_apy,
  -- predicted_retained_usd (retained_revenue of the chosen action)
  CASE
    WHEN ret_net >= xs_net AND ret_net >= rm_net THEN ret_retained
    WHEN xs_net >= ret_net AND xs_net >= rm_net THEN xs_retained
    ELSE rm_retained
  END AS predicted_retained_usd,
  -- predicted_net_value_usd (net_value of the chosen action)
  CASE
    WHEN ret_net >= xs_net AND ret_net >= rm_net THEN ret_net
    WHEN xs_net >= ret_net AND xs_net >= rm_net THEN xs_net
    ELSE rm_net
  END AS predicted_net_value_usd,
  -- action_ranking: JSON array of all 3 actions
  to_json(
    array(
      named_struct(
        'action', 'retention_offer',
        'retained_revenue', ret_retained,
        'net_value', ret_net,
        'cost', ret_cost
      ),
      named_struct(
        'action', 'cross_sell',
        'retained_revenue', xs_retained,
        'net_value', xs_net,
        'cost', CAST(50.0 AS DOUBLE)
      ),
      named_struct(
        'action', 'rm_outreach',
        'retained_revenue', rm_retained,
        'net_value', rm_net,
        'cost', CAST(40.0 AS DOUBLE)
      )
    )
  ) AS action_ranking,
  current_timestamp() AS scored_at
FROM with_net;
