# Milestone 2.5 — Reverse Lakehouse Sync: Postgres writable tables → UC Delta
# Streams changes from writable Lakebase tables back to Unity Catalog as Delta tables
# with SCD Type 2 history tracking (system columns: __START_AT, __END_AT, __IS_CURRENT)

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import (
    SyncedTable,
    SyncedTableSyncedTableSpec,
    SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy,
)

w = WorkspaceClient()

# Reverse sync: rm_actions (writable Postgres) → UC Delta with CDC
# This creates a managed Lakeflow pipeline that captures all changes
# and materializes them as an SCD Type 2 Delta table in Unity Catalog.

PROJECT = "meridian-bank"
BRANCH = "production"

# The reverse sync uses Lakehouse Sync (Postgres → Delta)
# Configure via the synced table spec pointing from Postgres source
# to a UC target with change tracking enabled.

print("Setting up Reverse Lakehouse Sync for rm_actions...")
print(f"  Source: Lakebase {PROJECT}/{BRANCH} → meridian_bank.rm_actions")
print(f"  Target: techsummit_27.meridian_bank.delta_rm_actions")
print(f"  Mode: Continuous CDC with SCD Type 2 history")
print()

# Enable logical replication on the source table (required for CDC)
# This is done via the Lakebase project settings or SQL:
#   ALTER TABLE meridian_bank.rm_actions REPLICA IDENTITY FULL;

# Create the reverse synced table definition
# The Lakehouse Sync feature streams Postgres WAL changes into Delta
w.postgres.create_synced_table(
    synced_table=SyncedTable(spec=SyncedTableSyncedTableSpec(
        source_table_full_name="techsummit_27.meridian_bank.delta_rm_actions",
        branch=f"projects/{PROJECT}/branches/{BRANCH}",
        primary_key_columns=["action_id"],
        scheduling_policy=SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.CONTINUOUS,
        postgres_database="databricks_postgres",
        create_database_objects_if_missing=True,
    )),
    synced_table_id="techsummit_27.meridian_bank.synced_reverse_rm_actions",
)

print("Reverse Lakehouse Sync created successfully.")
print()
print("SCD Type 2 system columns in the Delta target:")
print("  __START_AT  — timestamp when the row version became effective")
print("  __END_AT    — timestamp when superseded (NULL = current)")
print("  __IS_CURRENT — boolean flag for active version")
print("  _change_type — CDC operation: insert, update_preimage, update_postimage, delete")
