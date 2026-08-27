# Milestone 2 — Lakebase: Operational Database for Meridian Bank

## Project Details
- **Project:** meridian-bank
- **PG Version:** 17 (Autoscaling, scale-to-zero enabled)
- **Host:** ep-morning-art-e1k1x4aq.database.eastus2.azuredatabricks.net
- **Database:** databricks_postgres
- **Schema:** meridian_bank
- **Branches:** production, dev, agent-migration-001, forecasting-q3-2025

---

## ☑ Requirement Checklist

### Lakebase Instance + Connectivity
- **Script:** `01_create_project.py`
- **Evidence:** `outputs/01_project_creation.json`
- Lakebase project created with PG 17, autoscaling (0.5–2 CU)
- Connectivity verified: 12ms latency, SSL, PostgreSQL 17.2 confirmed

### UC Table Synced into Lakebase (Returns Rows)
- **Script:** `02_sync_gold_tables.py`
- **Evidence:** `outputs/02_sync_gold_tables.json`
- 3 gold tables synced (24,306 total rows), all ONLINE

### Operational Schema Modeled (Tables + Keys)
- **Script:** `03_create_writable_tables.sql`, `04_products_and_search.sql`
- **Evidence:** `outputs/03_writable_tables.json`, `outputs/04_products_search.json`
- `rm_actions`: PK action_id, FKs to customer_id, product references
- `products`: PK product_id, GIN search index, BM25 index

### Writable Tables (Distinct from Read-Only Synced)
- **Script:** `03_create_writable_tables.sql`
- **Evidence:** `outputs/03_writable_tables.json`
- `rm_actions` and `products` = writable (app-owned)
- `synced_gold_*` = read-only (managed by Lakehouse Sync)

### Reverse Lakehouse Sync (Postgres → UC Delta)
- **Script:** `05_reverse_lakehouse_sync.py`
- **Pipeline:** `pipelines/reverse_sync_rm_actions.sql`
- **Evidence:** `outputs/05_reverse_sync.json`
- Continuous CDC from rm_actions → delta_rm_actions_scd2

### Sync Defined as Code (DAB, Not UI-Only)
- **File:** `databricks.yml`
- Declarative Automation Bundle defining the reverse sync pipeline
- Deploy with `databricks bundle deploy --target prod`

### SCD Type 2 History + System Metadata Columns
- **Script:** `06_scd2_verification.sql`
- **Evidence:** `outputs/06_scd2_history.json`
- System columns: `__START_AT`, `__END_AT`, `_change_type`, `_commit_timestamp`
- Historical vs current records tracked

### Scale-to-Zero Configured
- **Script:** `01_create_project.py` (autoscaling spec)
- **Evidence:** `outputs/01_project_creation.json` → `scale_to_zero: true`
- Idle branches cost close to nothing

### Branching: Dev Iteration + Throwaway Forecasting
- **Script:** `10_branching_workflow.py`
- **Evidence:** `outputs/10_branching_workflow.json`
- `dev` — permanent, iterative development
- `forecasting-q3-2025` — 4h TTL, throwaway scenario analysis

### Coding Agent's Change as Diff/Migration
- **Script:** `07_agent_schema_migration.py`
- **Migration:** `migrations/001_add_retention_scoring.sql`
- **Evidence:** `outputs/07_agent_migration.json`
- Agent created branch, applied DDL, committed as versioned migration

### Agent's Change Validated by Test
- **Script:** `08_validate_migration.sql`
- **Evidence:** `outputs/08_validation.json`
- 5 tests: columns exist, insert works, index exists, index usable, cleanup
- All pass → ready for promotion

### Validated Change Promoted via Merge to Main
- **Script:** `11_promote_to_production.py`
- **Evidence:** `COMMIT_HISTORY.md`
- Migration applied to production after passing validation
- Agent branch auto-expires (clean history)

### Progressive Layered Build in Commit History
- **File:** `COMMIT_HISTORY.md`
- 12 commits, each building on the previous layer
- Infrastructure → Data → App → Search → Sync → Agent → Test → Promote

### Lakebase Search (Vector + Full-Text)
- **Script:** `04_products_and_search.sql`
- **Evidence:** `outputs/04_products_search.json`
- Extensions: `vector` → `lakebase_vector` → `lakebase_text`
- GIN tsvector index + BM25 index for hybrid search

### Search Query Returns Relevant Records
- **Evidence:** `outputs/04_products_search.json`
- Query "high yield savings" → High-Yield Savings (rank 0.099), Money Market (rank 0.061)
- Latency: 3ms

### Low-Latency Business Domain Query
- **Script:** `09_business_query.sql`
- **Evidence:** `outputs/09_business_query.json`
- Question: "Which high-value at-risk customers need RM action?"
- Joins synced + writable tables, returns top 5 at-risk customers with recommendations
- Latency: 23ms

---

## File Structure

```
milestone2_lakebase/
├── 00_prerequisites.sql          # UC permissions
├── 01_create_project.py          # Project + branches
├── 02_sync_gold_tables.py        # UC → Postgres sync
├── 03_create_writable_tables.sql # Writable rm_actions
├── 04_products_and_search.sql    # Products + search (pgvector fixed)
├── 05_reverse_lakehouse_sync.py  # Postgres → UC Delta (reverse sync)
├── 06_scd2_verification.sql      # SCD2 history proof
├── 07_agent_schema_migration.py  # Agent migration workflow
├── 08_validate_migration.sql     # Migration tests
├── 09_business_query.sql         # Domain question (low-latency)
├── 10_branching_workflow.py      # Dev + throwaway branches
├── 11_promote_to_production.py   # Merge to main
├── connection_reference.py       # OAuth connection pattern
├── databricks.yml                # DAB (sync as code)
├── COMMIT_HISTORY.md             # Progressive build evidence
├── README.md                     # This file
├── migrations/
│   └── 001_add_retention_scoring.sql  # Versioned DDL migration
├── pipelines/
│   └── reverse_sync_rm_actions.sql    # SDP pipeline definition
└── outputs/                      # Execution evidence
    ├── 01_project_creation.json
    ├── 02_sync_gold_tables.json
    ├── 03_writable_tables.json
    ├── 04_products_search.json
    ├── 05_reverse_sync.json
    ├── 06_scd2_history.json
    ├── 07_agent_migration.json
    ├── 08_validation.json
    ├── 09_business_query.json
    └── 10_branching_workflow.json
```

## Synced Tables (Snapshot mode, all ONLINE)
1. `synced_gold_customer_position` — PK: customer_id (8,742 rows)
2. `synced_gold_open_atrisk` — PK: customer_id, atrisk_product_id (3,156 rows)
3. `synced_gold_nba_recommendations` — PK: customer_id, recommended_action (12,408 rows)

## Writable Tables
1. `rm_actions` — RM-approved retention actions (with reverse sync to UC Delta)
2. `products` — Bank product catalog with hybrid search

## Branch Strategy
- **production** — protected, receives only validated promoted changes
- **dev** — permanent, for iterative schema/query development
- **agent-migration-*** — short-lived (24h), for AI agent schema changes
- **forecasting-*** — throwaway (4h), for ad-hoc scenario analysis
