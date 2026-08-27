# Milestone 2.9 — Low-Latency Business Domain Query (Direct Lakebase Connection)
# Connects directly to Lakebase Postgres via psycopg2 using OAuth credentials
# from the Databricks SDK — no Spark/Lakehouse intermediary.

from databricks.sdk import WorkspaceClient
import psycopg
import pandas as pd

# --- Lakebase connection parameters ---
PROJECT = "meridian-bank"
BRANCH = "production"
ENDPOINT = "primary"
DATABASE = "databricks_postgres"
HOST = "ep-morning-art-e1k1x4aq.database.eastus2.azuredatabricks.net"

# Generate short-lived OAuth credential via Databricks SDK
w = WorkspaceClient()
username = w.current_user.me().user_name
token = w.postgres.generate_database_credential(
    endpoint=f"projects/{PROJECT}/branches/{BRANCH}/endpoints/{ENDPOINT}"
).token

# --- Connect directly to Lakebase Postgres ---
conn = psycopg.connect(
    host=HOST,
    port=5432,
    dbname=DATABASE,
    user=username,
    password=token,
    sslmode="require",
)

# --- Business Query: High-value at-risk customers with NBA recommendations ---
query = """
SELECT
    cp.customer_id,
    cp.customer_display_name,
    cp.deposit_balance_usd,
    cp.tenure_years,
    cp.tier,
    ar.atrisk_product_id,
    ar.attrition_risk_score,
    ar.days_to_maturity,
    nba.recommended_action,
    nba.predicted_retained_usd,
    p.product_name AS recommended_product,
    p.rate_apy AS offer_rate
FROM meridian_bank.synced_gold_customer_position cp
JOIN meridian_bank.synced_gold_open_atrisk ar
    ON cp.customer_id = ar.customer_id
JOIN meridian_bank.synced_gold_nba_recommendations nba
    ON cp.customer_id = nba.customer_id
LEFT JOIN meridian_bank.products p
    ON nba.recommended_offer_product_id = p.product_id
WHERE cp.deposit_balance_usd > 100000
  AND ar.attrition_risk_score > 0.6
ORDER BY ar.attrition_risk_score DESC, cp.deposit_balance_usd DESC
LIMIT 10;
"""

with conn.cursor() as cur:
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

conn.close()

df = pd.DataFrame(rows, columns=columns)
print(f"✓ Returned {len(df)} high-risk customers from Lakebase (direct Postgres connection)")
print(df.to_string(index=False))
