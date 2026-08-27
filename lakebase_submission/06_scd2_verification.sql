-- Milestone 2.6 — Verify SCD Type 2 History in Reverse-Synced Delta Table
-- This query proves the reverse Lakehouse Sync produces proper SCD2 columns.
-- Run against: Unity Catalog (Databricks SQL)

-- 1. Show SCD Type 2 system metadata columns
SELECT
    action_id,
    customer_id,
    recommended_action,
    status,
    approved_by,
    approved_at,
    -- SCD Type 2 system columns added by APPLY CHANGES INTO ... STORED AS SCD TYPE 2
    __START_AT,     -- When this row version became effective
    __END_AT        -- When superseded (NULL = current active version)
FROM techsummit_27.meridian_bank.delta_rm_actions_scd2
ORDER BY action_id, __START_AT
LIMIT 20;

-- 2. Show version history for a single action (proves SCD2 tracking)
SELECT
    action_id,
    status,
    notes,
    __START_AT AS effective_from,
    __END_AT AS effective_until,
    CASE WHEN __END_AT IS NULL THEN 'CURRENT' ELSE 'HISTORICAL' END AS version_status
FROM techsummit_27.meridian_bank.delta_rm_actions_scd2
WHERE action_id = (
    SELECT action_id FROM techsummit_27.meridian_bank.delta_rm_actions_scd2 LIMIT 1
)
ORDER BY __START_AT;

-- 3. Count current vs historical records (proves versioning works)
SELECT
    CASE WHEN __END_AT IS NULL THEN 'current' ELSE 'historical' END AS record_type,
    COUNT(*) AS row_count
FROM techsummit_27.meridian_bank.delta_rm_actions_scd2
GROUP BY 1;

-- 4. Verify CDC metadata from the change feed
SELECT *
FROM table_changes('techsummit_27.meridian_bank.delta_rm_actions_scd2', 1)
ORDER BY _commit_timestamp DESC
LIMIT 10;
