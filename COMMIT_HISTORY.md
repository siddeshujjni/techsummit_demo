# Commit History — Progressive Layered Build

This file documents the progressive, layered development workflow.
Each commit builds on the previous one, demonstrating incremental construction.

## Commit Log (from `git log --all --oneline --graph`)

```
* 2909974 (dev/lakebase-milestone-2) feat(milestone-2.10): branching workflow with SDK credential fix
* b6e9edf (HEAD -> main, origin/main) branching fixed
* 88aaf9c code restructure
* a8171ea cleanup
* 3ffd055 outputs
* 0aab4e5 commit outputs
* bf6a9b3 changed python files to ipynb
* 89d744e feat: update business query to use direct Lakebase Postgres connection
* 34fd07b cleanup
*   3dded03 Merge remote-tracking branch 'origin/main'
|\  
| * 8499fe7 lakebase submission
* | 621e91f Merge Lakebase Milestone 2 content with AI Customer Retention upstream changes
|/  
* 2c6d34b Updated assets and refactored code structure
* 473a11e changed workspaces
* 4e14a7c Initial push from workspace without lakebase
```

## Detailed Commit Log

| Hash | Date | Author | Message |
|------|------|--------|---------|
| 2909974 | 2026-08-28 | ron.guerrero@databricks.com | feat(milestone-2.10): branching workflow with SDK credential fix |
| b6e9edf | 2026-08-28 | ron.guerrero@databricks.com | branching fixed |
| 88aaf9c | 2026-08-28 | ron guerrero | code restructure |
| a8171ea | 2026-08-28 | ron guerrero | cleanup |
| 3ffd055 | 2026-08-28 | ron.guerrero@databricks.com | outputs |
| 0aab4e5 | 2026-08-28 | ron.guerrero@databricks.com | commit outputs |
| bf6a9b3 | 2026-08-28 | ron.guerrero@databricks.com | changed python files to ipynb |
| 89d744e | 2026-08-27 | ron.guerrero@databricks.com | feat: update business query to use direct Lakebase Postgres connection |
| 34fd07b | 2026-08-27 | ron.guerrero@databricks.com | cleanup |
| 3dded03 | 2026-08-27 | ron.guerrero@databricks.com | Merge remote-tracking branch 'origin/main' |
| 8499fe7 | 2026-08-27 | ron guerrero | lakebase submission |
| 621e91f | 2026-08-27 | ron.guerrero@databricks.com | Merge Lakebase Milestone 2 content with AI Customer Retention upstream changes |
| 2c6d34b | 2026-08-27 | devanshu.pandey@databricks.com | Updated assets and refactored code structure |
| 473a11e | 2026-08-27 | devanshu.pandey@databricks.com | changed workspaces |
| 4e14a7c | 2026-08-27 | dpandey-db | Initial push from workspace without lakebase |

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
