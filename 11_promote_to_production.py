# Milestone 2.11 — Promote Validated Migration to Production
# After tests pass on agent-migration-001, apply the migration to production.
# This demonstrates: main stays clean until promotion.

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

PROJECT = "meridian-bank"
HOST = "ep-morning-art-e1k1x4aq.database.eastus2.azuredatabricks.net"

print("Promoting migration 001 to production...")
print("  Source: agent-migration-001 (validated)")
print("  Target: production")
print()

# Step 1: Connect to production and apply the validated migration
cred = w.postgres.generate_database_credential(
    endpoint=f"projects/{PROJECT}/branches/production/endpoints/primary"
)

import psycopg2
conn = psycopg2.connect(
    host=HOST, port=5432, dbname="databricks_postgres",
    user=cred.username, password=cred.password, sslmode="require",
)
conn.autocommit = True

# Read and apply the versioned migration file
with open("migrations/001_add_retention_scoring.sql", "r") as mf:
    migration_sql = mf.read()

with conn.cursor() as cur:
    cur.execute(migration_sql)
    print("  ✓ Migration 001 applied to production")

    # Verify on production
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'meridian_bank' AND table_name = 'rm_actions'
        AND column_name IN ('retention_probability', 'model_version', 'scored_at')
    """)
    print("  ✓ Verified columns on production:")
    for row in cur.fetchall():
        print(f"      {row[0]}: {row[1]}")

conn.close()

# Step 2: The agent-migration-001 branch expires (24h TTL)
# Production is now the single source of truth
print()
print("  ✓ Production updated — main stays clean")
print("  ✓ agent-migration-001 will auto-expire (TTL)")
print()
print("Git workflow:")
print("  1. Agent created migration on isolated branch")
print("  2. Tests ran and passed on that branch")
print("  3. Migration promoted to production (this script)")
print("  4. Branch expires — zero cost, clean history")
