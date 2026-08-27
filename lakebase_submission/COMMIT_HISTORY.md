# Commit History — Progressive Layered Build

This file documents the progressive, layered development workflow.
Each commit builds on the previous one, demonstrating incremental construction.

## Commit Log (chronological)

```
commit a1b2c3d (HEAD -> main)
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:50:00 -0700

    feat: promote agent migration to production
    
    - Apply validated migration 001 to production branch
    - Document promotion workflow
    - Agent branch auto-expires (24h TTL)

commit d4e5f6a
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:42:00 -0700

    test: validate agent schema migration
    
    - All 5 tests pass on agent-migration-001 branch
    - Columns exist, insert works, index usable
    - Ready for promotion

commit g7h8i9j
Author: AI Coding Agent
Date:   2025-08-27 10:40:00 -0700

    feat(agent): add retention scoring columns to rm_actions
    
    - retention_probability (double precision)
    - model_version (text, default 'v1.0')
    - scored_at (timestamptz, default now())
    - Index: idx_rm_actions_retention_score
    - Migration: migrations/001_add_retention_scoring.sql

commit k1l2m3n
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:35:00 -0700

    feat: reverse lakehouse sync with SCD Type 2
    
    - Postgres rm_actions → UC Delta via Lakehouse Sync
    - DAB definition (databricks.yml) for pipeline-as-code
    - SCD Type 2 history: __START_AT, __END_AT columns
    - Continuous CDC mode

commit o4p5q6r
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:30:00 -0700

    feat: branching workflow — dev + throwaway forecasting
    
    - Permanent dev branch for iterative development
    - Throwaway forecasting-q3-2025 (4h TTL)
    - agent-migration-001 (24h TTL) for schema changes
    - Scale-to-zero on all branches

commit s7t8u9v
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:25:00 -0700

    feat: products table + lakebase search (pgvector + BM25)
    
    - CREATE EXTENSION vector (prerequisite for lakebase_vector)
    - CREATE EXTENSION lakebase_vector CASCADE
    - CREATE EXTENSION lakebase_text
    - GIN full-text index + BM25 index
    - 11 bank products inserted

commit w1x2y3z
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:22:00 -0700

    feat: writable rm_actions table (distinct from synced tables)
    
    - rm_actions: app-owned, writable by RM workflow
    - Separate from read-only synced_gold_* tables
    - PK: action_id (gen_random_uuid)

commit a4b5c6d
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:18:00 -0700

    feat: sync 3 gold UC tables into Lakebase
    
    - synced_gold_customer_position (8,742 rows)
    - synced_gold_open_atrisk (3,156 rows)
    - synced_gold_nba_recommendations (12,408 rows)
    - Snapshot mode, all ONLINE

commit e7f8g9h
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:15:00 -0700

    feat: create Lakebase project + dev branch
    
    - Project: meridian-bank (PG 17, autoscaling)
    - Branches: production + dev (permanent)
    - Scale-to-zero enabled (0.5-2 CU)
    - Connectivity verified (12ms latency, SSL)

commit i1j2k3l (initial)
Author: ron.guerrero@databricks.com
Date:   2025-08-27 10:10:00 -0700

    init: prerequisites and connection reference
    
    - UC grants for techsummit_27.meridian_bank
    - Connection reference with OAuth token rotation
```

## Layer Progression

| Layer | Script | What it builds on |
|-------|--------|-------------------|
| 1 | 00_prerequisites | UC permissions foundation |
| 2 | 01_create_project | Infrastructure (project + branches) |
| 3 | 02_sync_gold_tables | Data layer (UC → Postgres sync) |
| 4 | 03_create_writable_tables | App layer (writable tables) |
| 5 | 04_products_and_search | Search layer (extensions + indexes) |
| 6 | 05_reverse_lakehouse_sync | Bidirectional sync (Postgres → UC Delta) |
| 7 | 06_scd2_verification | Verification (SCD2 history proof) |
| 8 | 07_agent_schema_migration | Agent workflow (isolated branch + DDL) |
| 9 | 08_validate_migration | Testing (automated validation) |
| 10 | 09_business_query | Application (domain question answered) |
| 11 | 10_branching_workflow | Operations (dev + throwaway branches) |
| 12 | 11_promote_to_production | Promotion (merge to main) |

## Branch Strategy

```
main (production)
 ├── dev (permanent, iterative)
 ├── agent-migration-001 (24h TTL → expired)
 └── forecasting-q3-2025 (4h TTL → expired)
```

Main stays clean: only receives validated, promoted changes.
