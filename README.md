# Meridian Bank — AI Customer Retention Challenge

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

## Catalog & Schema
- **Catalog**: `oh_phi_workspace`
- **Schema**: `meridian_bank`
- **Volume**: `/Volumes/oh_phi_workspace/meridian_bank/raw_data/`

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
| Pipeline | `92a033db-7bcf-4244-87f3-575ce28a22a0` |
| Dashboard | `01f1a227f05f139999d6e8507c1cc9eb` |
| Genie Space | `01f1a228dd83154c9c7d24155991b693` |

## Files
- `transformations/silver.sql` — Silver layer materialized views
- `transformations/gold.sql` — Gold layer materialized views
- `transformations/metric_view.sql` — Metric view definition
- `genie_space.json` — Genie space configuration
- `resources.json` — Deployed asset IDs
