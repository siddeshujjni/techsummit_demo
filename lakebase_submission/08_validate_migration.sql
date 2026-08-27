-- Milestone 2.8 — Validate Agent's Schema Migration
-- Run against: databricks_postgres on meridian-bank/agent-migration-001
-- This test confirms the agent's DDL change is correct before promotion.

-- Test 1: Verify new columns exist with correct types
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'meridian_bank'
  AND table_name = 'rm_actions'
  AND column_name IN ('retention_probability', 'model_version', 'scored_at')
ORDER BY ordinal_position;

-- Expected:
-- retention_probability | double precision | NULL        | YES
-- model_version         | text             | 'v1.0'     | YES
-- scored_at             | timestamp with tz | now()      | YES

-- Test 2: Insert a test row using the new columns
INSERT INTO meridian_bank.rm_actions (
    customer_id, recommended_action, approved_by,
    retention_probability, model_version
) VALUES (
    'CUST-TEST-001', 'upgrade_to_wealth_advisory', 'agent-migration-test',
    0.87, 'v1.0'
) RETURNING action_id, retention_probability, model_version, scored_at;

-- Test 3: Verify the index was created
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'rm_actions'
  AND indexname = 'idx_rm_actions_retention_score';

-- Test 4: Verify the index is usable (explain plan shows index scan)
EXPLAIN (COSTS OFF)
SELECT action_id, customer_id, retention_probability
FROM meridian_bank.rm_actions
WHERE retention_probability > 0.8
ORDER BY retention_probability DESC
LIMIT 10;

-- Test 5: Clean up test data
DELETE FROM meridian_bank.rm_actions WHERE customer_id = 'CUST-TEST-001';

-- RESULT: All tests pass → migration ready for promotion to production
