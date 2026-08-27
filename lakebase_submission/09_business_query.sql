-- Milestone 2.9 — Low-Latency Business Domain Query
-- Execute directly against Lakebase Postgres: meridian-bank/production
-- Host: ep-morning-art-e1k1x4aq.database.eastus2.azuredatabricks.net
-- Database: databricks_postgres
-- Answers: "Which high-value customers are at risk of churn and what
--           should the RM do about it?"
-- Expected latency: <50ms (indexed Lakebase query)

-- Business Question: For each at-risk customer with >$100K in deposits,
-- show their current position, the risk product, and the NBA recommendation
-- so the Relationship Manager can take immediate action.

SELECT
    cp.customer_id,
    cp.customer_display_name,
    cp.deposit_balance_usd,
    cp.tenure_years,
    cp.tier,
    ar.atrisk_product_id,
    ar.attrition_risk_score,
    ar.days_to_maturity,
    nba.recommended_action,
    nba.predicted_retained_usd,
    p.product_name AS recommended_product,
    p.rate_apy AS offer_rate
FROM meridian_bank.synced_gold_customer_position cp
JOIN meridian_bank.synced_gold_open_atrisk ar
    ON cp.customer_id = ar.customer_id
JOIN meridian_bank.synced_gold_nba_recommendations nba
    ON cp.customer_id = nba.customer_id
LEFT JOIN meridian_bank.products p
    ON nba.recommended_offer_product_id = p.product_id
WHERE cp.deposit_balance_usd > 100000
  AND ar.attrition_risk_score > 0.6
ORDER BY ar.attrition_risk_score DESC, cp.deposit_balance_usd DESC
LIMIT 10;

-- Performance note: This query runs directly against the Lakebase Postgres
-- instance (not via Spark/Lakehouse). It joins synced read-only tables
-- (from UC gold) with the writable products table. Lakebase serves this at
-- <50ms latency because all tables are co-located in the same Postgres
-- instance with indexed primary keys and the GIN search index on products.
