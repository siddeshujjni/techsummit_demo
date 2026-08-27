-- Lakeflow Spark Declarative Pipeline: Reverse Lakehouse Sync
-- Streams Postgres rm_actions changes into UC Delta with SCD Type 2 history
-- Deployed via Declarative Automation Bundle (databricks.yml)

-- Bronze: raw CDC stream from Lakebase Postgres via Lakehouse Sync
CREATE OR REFRESH STREAMING TABLE bronze_rm_actions
COMMENT 'Raw CDC stream from Lakebase rm_actions via Lakehouse Sync'
AS SELECT *
FROM STREAM read_changefeed('techsummit_27.meridian_bank.synced_reverse_rm_actions');

-- Silver: SCD Type 2 materialization with system metadata columns
CREATE OR REFRESH STREAMING TABLE delta_rm_actions_scd2 (
  CONSTRAINT valid_action_id EXPECT (action_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_customer EXPECT (customer_id IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'SCD Type 2 history of RM actions from Lakebase — tracks all state changes'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'quality' = 'silver',
  'pipelines.autoOptimize.managed' = 'true'
);

APPLY CHANGES INTO delta_rm_actions_scd2
FROM STREAM(bronze_rm_actions)
KEYS (action_id)
SEQUENCE BY approved_at
STORED AS SCD TYPE 2;
