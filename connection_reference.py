# Connection Reference — How to connect to Lakebase from an app or notebook
# Uses OAuth token from Databricks SDK (auto-rotates every hour)

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Get connection details
PROJECT = "meridian-bank"
BRANCH = "production"
ENDPOINT = "primary"
DATABASE = "databricks_postgres"
HOST = "ep-morning-art-e1k1x4aq.database.eastus2.azuredatabricks.net"

# Generate short-lived OAuth credential
cred = w.postgres.generate_database_credential(
    endpoint=f"projects/{PROJECT}/branches/{BRANCH}/endpoints/{ENDPOINT}"
)

# Connect with psycopg2
import psycopg2
conn = psycopg2.connect(
    host=HOST,
    port=5432,
    dbname=DATABASE,
    user=cred.username,
    password=cred.password,
    sslmode="require",
)

# Example query
with conn.cursor() as cur:
    cur.execute("SELECT count(*) FROM meridian_bank.synced_gold_customer_position")
    print(cur.fetchone())

conn.close()
