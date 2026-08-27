# Databricks notebook source
# MAGIC %md
# MAGIC # Configure Genie Space — Meridian Customer Retention
# MAGIC Creates (or updates) the Genie space with tables, instructions, and sample questions.
# MAGIC Requires: gold tables materialized + metric view created.

# COMMAND ----------

import json, requests

CATALOG = "techsummit_27"
SCHEMA = "meridian_bank"

# Load config
with open("/Workspace/Shared/techsummit_demo/config/genie_space.json") as f:
    config = json.load(f)

# Workspace host + token
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
host = ctx.apiUrl().get()
token = ctx.apiToken().get()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create or find existing Genie Space

# COMMAND ----------

TABLE_IDENTIFIERS = [
    f"{CATALOG}.{SCHEMA}.mv_customer_risk",
    f"{CATALOG}.{SCHEMA}.gold_customer_position",
    f"{CATALOG}.{SCHEMA}.gold_open_atrisk",
    f"{CATALOG}.{SCHEMA}.gold_nba_recommendations",
]

# Check if space already exists (by title)
resp = requests.get(f"{host}/api/2.0/genie/spaces", headers=headers)
spaces = resp.json().get("spaces", [])
existing = next((s for s in spaces if s.get("title") == config["title"]), None)

if existing:
    space_id = existing["id"]
    print(f"Found existing Genie space: {space_id}")
else:
    # Create new space
    payload = {
        "title": config["title"],
        "description": config["description"],
        "table_identifiers": TABLE_IDENTIFIERS,
    }
    resp = requests.post(f"{host}/api/2.0/genie/spaces", headers=headers, json=payload)
    resp.raise_for_status()
    space_id = resp.json()["space_id"]
    print(f"Created Genie space: {space_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configure instructions + sample questions

# COMMAND ----------

INSTRUCTIONS = """You analyze Meridian Bank customer-retention data for Marcus Bell (EVP Consumer & Small Business Banking, non-technical).

CONTEXT: A competitor launched a savings-rate promotion ~3 weeks ago aimed at maturing CDs and
high-balance savings. The bank's most valuable, longest-tenured customers holding those affected
deposits (18-Month CD PROD-DEP-2001 + 2 others) have slid into elevated attrition risk — ~220
critical customers with balance starting to flow out — while the rest of the ~40K-customer book is
stable. High value, rising risk, concentrated in a recent window.

BASELINES: A healthy customer sits at attrition_risk_score ~0.05-0.25. risk_band is the single
signal: 'critical' (risk >= 0.75 with balance at risk), 'elevated' (>= 0.6), 'watch' (>= 0.4),
'healthy'. Balance-at-risk and revenue-at-risk are only non-zero for at-risk customers.

HEADLINE NUMBERS — always answer from mv_customer_risk (same definitions the dashboard tiles use):
- "How much balance is at risk?" -> MEASURE(balance_at_risk)
- "What's our revenue at risk?" -> MEASURE(revenue_at_risk)
- "How many customers are critical?" -> MEASURE(critical_count)

INVESTIGATION FLOW for "who is at risk and why?":
1. mv_customer_risk -> MEASURE(critical_count) + MEASURE(atrisk_count) by tier -> affluent/private dominate
2. gold_customer_position -> at-risk cluster confined to high-value tiers holding affected deposits
3. gold_open_atrisk WHERE customer_id='CUST-0000214' -> the hero: large CD maturing in ~9 days
4. gold_nba_recommendations -> recommended next-best-action + predicted retained $
"""

# Update space with instructions and sample questions
patch_payload = {
    "description": config["description"],
    "config": {
        "sample_questions": config["sample_questions"],
        "instructions": {
            "text_instructions": [{"text": INSTRUCTIONS}]
        },
        "example_question_sqls": config.get("example_sqls", []),
    }
}

resp = requests.patch(
    f"{host}/api/2.0/genie/spaces/{space_id}",
    headers=headers,
    json=patch_payload
)
if resp.status_code == 200:
    print(f"✓ Genie space configured: {space_id}")
else:
    print(f"Warning: PATCH returned {resp.status_code}: {resp.text}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Update resources.json

# COMMAND ----------

resources_path = "/Workspace/Shared/techsummit_demo/resources.json"
with open(resources_path) as f:
    resources = json.load(f)

resources["genie_space_id"] = space_id
resources["genie_space_name"] = config["title"]

with open(resources_path, "w") as f:
    json.dump(resources, f, indent=2)

print(f"✓ Updated resources.json with genie_space_id: {space_id}")

# COMMAND ----------

print(f"\n=== Genie Space Ready ===")
print(f"  Space ID: {space_id}")
print(f"  Title: {config['title']}")
print(f"  Tables: {len(TABLE_IDENTIFIERS)}")
print(f"  Sample questions: {len(config['sample_questions'])}")
