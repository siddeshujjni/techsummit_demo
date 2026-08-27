# Meridian Bank — AI Customer Retention

A governed data layer + AI/BI dashboard + Genie space for Meridian Bank's customer attrition prevention.

## Problem Statement

A competitor rate promotion ~3 weeks ago pushed ~220 affluent/private customers with maturing CDs into high attrition risk.
- **Balance at risk**: ~$159M
- **Revenue at risk**: ~$4.1M
- **Critical customers**: ~220

## Architecture

```
Raw Parquet (UC Volume)
    └── SDP Pipeline (meridian_customer_360)
          ├── Silver: note_churn_flags, silver_holdings, silver_risk, silver_campaigns
          └── Gold: gold_customer_position, gold_open_atrisk, gold_campaign_outcomes, gold_nba_recommendations
                └── Metric View: mv_customer_risk
                      ├── AI/BI Dashboard (Meridian Customer Retention)
                      └── Genie Space (Meridian Customer Retention)
```

## Repository Structure

```
├── README.md                           # This file
├── resources.json                      # Deployed asset IDs (pipeline, dashboard, Genie)
│
├── src/
│   ├── pipeline/                       # SDP pipeline SQL (referenced by pipeline libraries[])
│   │   ├── silver.sql                  # Silver materialized views (4)
│   │   └── gold.sql                    # Gold materialized views (4)
│   │
│   └── setup/                          # One-time setup scripts (run as notebooks)
│       ├── 00_generate_data.py         # Synthetic data generation → UC Volume
│       ├── 01_create_metric_view.sql   # Metric view DDL (standalone, not pipeline)
│       └── 02_configure_genie.py       # Genie space creation + instructions
│
├── config/
│   └── genie_space.json                # Genie instructions, sample questions, example SQLs
│
└── dashboards/
    └── meridian_retention.lvdash.json  # Exported AI/BI dashboard (version-controlled)
```

## Deployment (manual — run in order)

1. **Generate raw data** — Run `src/setup/00_generate_data.py` as a notebook
2. **Run pipeline** — Trigger pipeline `meridian_customer_360` (creates silver + gold tables)
3. **Create metric view** — Run `src/setup/01_create_metric_view.sql`
4. **Import dashboard** — Upload `dashboards/meridian_retention.lvdash.json` via Lakeview API
5. **Configure Genie** — Run `src/setup/02_configure_genie.py`

## Catalog & Schema

- **Catalog**: `techsummit_27`
- **Schema**: `meridian_bank`
- **Volume**: `/Volumes/techsummit_27/meridian_bank/raw_data/`

## Key Tables

| Table | Description |
|-------|-------------|
| `gold_customer_position` | One row per customer — current risk, balance, band |
| `gold_open_atrisk` | At-risk customers with affected holding details |
| `gold_nba_recommendations` | Ranked next-best-action per at-risk customer |
| `mv_customer_risk` | Metric view for dashboard KPIs and Genie |

## Hero Customer

`CUST-0000214` — affluent, 12-year tenure, $650K 18-month CD maturing in ~9 days, Dallas TX

## Deployed Assets

| Asset | ID |
|-------|-----|
| Pipeline | `7ef9f037-4f92-42f9-84cb-dbc59441de74` |
| Dashboard | `01f1a238a10b17b9ab60da11ad1e67ac` |
| Genie Space | `01f1a23899dc1441a01de338fa0482c7` |
