# Milestone 2.10 — Branching Workflow: Dev Iteration + Throwaway Forecasting
# Demonstrates both branch use cases required:
#   1. Development iteration (permanent dev branch)
#   2. Throwaway forecasting branch (expires after analysis)

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import Branch, BranchSpec, Duration

w = WorkspaceClient()

PROJECT = "meridian-bank"
HOST = "ep-morning-art-e1k1x4aq.database.eastus2.azuredatabricks.net"

# ─── Use Case 1: Development Iteration on 'dev' branch ───
print("=" * 60)
print("USE CASE 1: Development Iteration (permanent dev branch)")
print("=" * 60)

# The dev branch was created in 01_create_project.py (no_expiry=True)
# Show it's active and being used for iterative development
for b in w.postgres.list_branches(parent=f"projects/{PROJECT}"):
    state = b.status.current_state if b.status else "UNKNOWN"
    print(f"  {b.name.split('/')[-1]:20s} — state: {state}")

# Connect to dev branch and show iterative work
cred = w.postgres.generate_database_credential(
    endpoint=f"projects/{PROJECT}/branches/dev/endpoints/primary"
)

import psycopg2
conn = psycopg2.connect(
    host=HOST, port=5432, dbname="databricks_postgres",
    user=cred.username, password=cred.password, sslmode="require",
)
conn.autocommit = True

with conn.cursor() as cur:
    # Iterative development: test schema changes on dev before production
    cur.execute("""
        SELECT table_name, pg_size_pretty(pg_total_relation_size(
            quote_ident(table_schema) || '.' || quote_ident(table_name)
        )) as size
        FROM information_schema.tables
        WHERE table_schema = 'meridian_bank'
        ORDER BY table_name
    """)
    print("\n  Tables on dev branch:")
    for row in cur.fetchall():
        print(f"    {row[0]:40s} {row[1]}")

conn.close()

# ─── Use Case 2: Throwaway Forecasting Branch ───
print("\n" + "=" * 60)
print("USE CASE 2: Throwaway Forecasting Branch (4h TTL)")
print("=" * 60)

# Create a short-lived branch for ad-hoc forecasting analysis
print("  Creating throwaway branch: forecasting-q3-2025...")
w.postgres.create_branch(
    parent=f"projects/{PROJECT}",
    branch=Branch(spec=BranchSpec(
        source_branch=f"projects/{PROJECT}/branches/production",
        ttl=Duration(seconds=14400),  # 4 hours — auto-deletes after
    )),
    branch_id="forecasting-q3-2025",
).wait()
print("  Created: forecasting-q3-2025 (TTL: 4 hours)")

# Connect to forecasting branch for analysis
cred_fc = w.postgres.generate_database_credential(
    endpoint=f"projects/{PROJECT}/branches/forecasting-q3-2025/endpoints/primary"
)
conn_fc = psycopg2.connect(
    host=HOST, port=5432, dbname="databricks_postgres",
    user=cred_fc.username, password=cred_fc.password, sslmode="require",
)
conn_fc.autocommit = True

with conn_fc.cursor() as cur:
    # Run a forecasting scenario — this is throwaway analysis
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meridian_bank.forecast_scenarios (
            scenario_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            scenario_name TEXT NOT NULL,
            assumptions JSONB,
            projected_retention_rate DOUBLE PRECISION,
            projected_revenue_impact_usd DOUBLE PRECISION,
            created_at TIMESTAMPTZ DEFAULT now()
        );

        INSERT INTO meridian_bank.forecast_scenarios
            (scenario_name, assumptions, projected_retention_rate, projected_revenue_impact_usd)
        VALUES
            ('aggressive_rate_match', '{"rate_increase_bps": 50, "target_segment": "affluent"}', 0.92, 2400000),
            ('moderate_engagement', '{"touchpoints": 3, "channel": "advisor"}', 0.78, 1600000),
            ('baseline_do_nothing', '{"action": "none"}', 0.61, 900000);
    """)
    
    cur.execute("SELECT scenario_name, projected_retention_rate, projected_revenue_impact_usd FROM meridian_bank.forecast_scenarios ORDER BY projected_retention_rate DESC")
    print("\n  Forecasting scenarios (throwaway analysis):")
    for row in cur.fetchall():
        print(f"    {row[0]:25s} retention={row[1]:.0%}  revenue_impact=${row[2]:,.0f}")

conn_fc.close()

print("\n  Branch 'forecasting-q3-2025' will auto-expire in 4 hours.")
print("  Production is unaffected — zero-cost isolation.")

# ─── Summary ───
print("\n" + "=" * 60)
print("BRANCHING SUMMARY")
print("=" * 60)
print("  dev                    — permanent, iterative development")
print("  agent-migration-001   — 24h TTL, agent schema changes")
print("  forecasting-q3-2025   — 4h TTL, throwaway scenario analysis")
print("  production             — protected, receives promoted changes only")
