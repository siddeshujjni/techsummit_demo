# Milestone 2.2 — Sync Gold Tables into Lakebase
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import (
    SyncedTable,
    SyncedTableSyncedTableSpec,
    SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy,
)

w = WorkspaceClient()

SYNCED_TABLES = [
    {
        "source": "techsummit_27.meridian_bank.gold_customer_position",
        "id": "techsummit_27.meridian_bank.synced_gold_customer_position",
        "pk": ["customer_id"],
    },
    {
        "source": "techsummit_27.meridian_bank.gold_open_atrisk",
        "id": "techsummit_27.meridian_bank.synced_gold_open_atrisk",
        "pk": ["customer_id", "atrisk_product_id"],
    },
    {
        "source": "techsummit_27.meridian_bank.gold_nba_recommendations",
        "id": "techsummit_27.meridian_bank.synced_gold_nba_recommendations",
        "pk": ["customer_id", "recommended_action"],
    },
]

for table in SYNCED_TABLES:
    print(f"Syncing {table['source']}...")
    w.postgres.create_synced_table(
        synced_table=SyncedTable(spec=SyncedTableSyncedTableSpec(
            source_table_full_name=table["source"],
            branch="projects/meridian-bank/branches/production",
            primary_key_columns=table["pk"],
            scheduling_policy=SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.SNAPSHOT,
            postgres_database="databricks_postgres",
            create_database_objects_if_missing=True,
        )),
        synced_table_id=table["id"],
    )
    print(f"  Done: {table['id']}")
