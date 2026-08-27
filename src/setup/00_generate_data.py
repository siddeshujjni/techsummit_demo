# Databricks notebook source
# MAGIC %md
# MAGIC # Meridian Bank — Raw Data Generation
# MAGIC Generates 6 synthetic datasets for the customer retention demo.
# MAGIC Run once to seed `/Volumes/techsummit_27/meridian_bank/raw_data/`.

# COMMAND ----------

CATALOG = "techsummit_27"
SCHEMA = "meridian_bank"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/raw_data"

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS raw_data")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Products (reference table — 11 rows)

# COMMAND ----------

from pyspark.sql import Row
from pyspark.sql.functions import when, col

products = [
    ("PROD-DEP-2001", "18-Month CD",        "deposit",    0.0325, "mass_affluent"),
    ("PROD-DEP-2002", "12-Month CD",        "deposit",    0.0300, "mass"),
    ("PROD-DEP-2003", "24-Month CD",        "deposit",    0.0350, "affluent"),
    ("PROD-DEP-1001", "High-Yield Savings", "deposit",    0.0290, "mass"),
    ("PROD-DEP-1002", "Premium Savings",    "deposit",    0.0310, "affluent"),
    ("PROD-CHK-1001", "Core Checking",      "checking",   0.0010, "mass"),
    ("PROD-CHK-1002", "Premium Checking",   "checking",   0.0050, "affluent"),
    ("PROD-INV-3001", "Managed Portfolio",  "investment", 0.0000, "affluent"),
    ("PROD-INV-3002", "Self-Directed IRA",  "investment", 0.0000, "mass_affluent"),
    ("PROD-CRD-4001", "Rewards Credit Card","lending",    0.1899, "mass"),
    ("PROD-LN-5001",  "Home Equity Line",   "lending",    0.0650, "mass_affluent"),
]
products_df = spark.createDataFrame(
    [Row(product_id=p[0], product_name=p[1], product_type=p[2],
         segment=("deposit" if p[2] == "checking" else p[2]),
         rate_apy=p[3], target_segment=p[4]) for p in products]
)
products_df.write.mode("overwrite").parquet(f"{VOLUME_PATH}/products")
print(f"products: {products_df.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Customers (40,000)

# COMMAND ----------

import random
from pyspark.sql.types import *
from datetime import date, timedelta

random.seed(42)
TIERS = ["mass", "mass_affluent", "affluent", "private"]
TIER_WEIGHTS = [0.50, 0.25, 0.15, 0.10]
METROS = [
    ("Dallas TX", 32.78, -96.80), ("Houston TX", 29.76, -95.37),
    ("New York NY", 40.71, -74.01), ("Los Angeles CA", 34.05, -118.24),
    ("Chicago IL", 41.88, -87.63), ("Miami FL", 25.76, -80.19),
    ("San Francisco CA", 37.77, -122.42), ("Boston MA", 42.36, -71.06),
    ("Atlanta GA", 33.75, -84.39), ("Denver CO", 39.74, -104.99),
]
FIRST_NAMES = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","David","Elizabeth",
               "William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
              "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"]

def gen_customer(i):
    tier = random.choices(TIERS, TIER_WEIGHTS)[0]
    metro = random.choice(METROS)
    tenure = random.randint(1, 25) if tier in ("affluent", "private") else random.randint(1, 15)
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    lat = round(metro[1] + random.uniform(-0.5, 0.5), 6)
    lng = round(metro[2] + random.uniform(-0.5, 0.5), 6)
    profile = f"{tier.replace('_',' ').title()} client, {tenure}yr tenure, {metro[0]}. "
    profile += "High-value relationship with multiple product lines." if tier in ("affluent","private") else "Standard banking relationship."
    return (f"CUST-{i:07d}", name, tier, tenure, metro[0], lat, lng, profile)

customer_data = [gen_customer(i) for i in range(40000)]
customers_df = spark.createDataFrame(customer_data, schema=StructType([
    StructField("customer_id", StringType()), StructField("customer_display_name", StringType()),
    StructField("tier", StringType()), StructField("tenure_years", IntegerType()),
    StructField("home_metro", StringType()), StructField("customer_lat", DoubleType()),
    StructField("customer_lng", DoubleType()), StructField("profile_summary", StringType()),
]))
customers_df.write.mode("overwrite").parquet(f"{VOLUME_PATH}/customers")
print(f"customers: {customers_df.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Holdings (~120K)

# COMMAND ----------

random.seed(43)
AFFECTED_PRODUCTS = ["PROD-DEP-2001", "PROD-DEP-2002", "PROD-DEP-2003"]
ALL_PRODUCTS = [p[0] for p in products]
TODAY = date.today()

holdings_data = []
for cust in customer_data:
    cid, _, tier, tenure, _, _, _, _ = cust
    n_products = random.randint(2, 5) if tier in ("affluent", "private") else random.randint(1, 3)
    held = random.sample(ALL_PRODUCTS, min(n_products, len(ALL_PRODUCTS)))
    cust_idx = int(cid.split("-")[1])
    if cust_idx % 37 == 0 and tier in ("affluent", "private"):
        if "PROD-DEP-2001" not in held:
            held[0] = "PROD-DEP-2001"
    for j, pid in enumerate(held):
        prod_info = next((p for p in products if p[0] == pid), None)
        if pid in AFFECTED_PRODUCTS and tier in ("affluent", "private"):
            balance = random.uniform(200000, 900000)
            maturity = (TODAY + timedelta(days=random.randint(5, 45))).isoformat()
        elif "DEP" in pid or "CHK" in pid:
            balance = random.uniform(5000, 150000)
            maturity = (TODAY + timedelta(days=random.randint(30, 365))).isoformat() if "DEP" in pid else None
        elif "INV" in pid:
            balance = random.uniform(50000, 500000); maturity = None
        else:
            balance = random.uniform(1000, 50000); maturity = None
        rate = prod_info[3] if prod_info else 0.01
        holdings_data.append((f"ACCT-{cust_idx:07d}-{j:02d}", cid, pid, round(balance,2), maturity, rate, "active"))

holdings_df = spark.createDataFrame(holdings_data, schema=StructType([
    StructField("account_id", StringType()), StructField("customer_id", StringType()),
    StructField("product_id", StringType()), StructField("balance_usd", DoubleType()),
    StructField("maturity_date", StringType()), StructField("rate_apy", DoubleType()),
    StructField("status", StringType()),
]))
holdings_df.write.mode("overwrite").parquet(f"{VOLUME_PATH}/holdings")
print(f"holdings: {holdings_df.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Transactions (~3.5M)

# COMMAND ----------

random.seed(44)
txn_data = []
txn_counter = 0
for cust in customer_data:
    cid, _, tier, _, _, _, _, _ = cust
    n_txn = random.randint(50, 120) if tier in ("affluent", "private") else random.randint(30, 80)
    for _ in range(n_txn):
        txn_date = (TODAY - timedelta(days=random.randint(0, 180))).isoformat()
        txn_type = random.choice(["debit", "credit", "transfer", "fee", "interest"])
        amount = round(random.uniform(10, 5000) if txn_type != "fee" else random.uniform(5, 50), 2)
        channel = random.choice(["mobile", "web", "branch", "atm", "wire"])
        txn_data.append((f"TXN-{txn_counter:010d}", cid, txn_date, txn_type, amount, channel))
        txn_counter += 1

txn_df = spark.createDataFrame(txn_data, schema=StructType([
    StructField("transaction_id", StringType()), StructField("customer_id", StringType()),
    StructField("transaction_date", StringType()), StructField("transaction_type", StringType()),
    StructField("amount_usd", DoubleType()), StructField("channel", StringType()),
]))
txn_df.write.mode("overwrite").parquet(f"{VOLUME_PATH}/transactions")
print(f"transactions: {txn_df.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Risk Snapshots (~42K)

# COMMAND ----------

random.seed(45)
NOTES_CHURN = ["Client mentioned exploring competitor rates","Customer asked about early withdrawal penalties",
    "Expressed dissatisfaction with current CD yield","Inquired about transferring funds to external account",
    "Mentioned competitor offering 3.85% on savings"]
NOTES_ATRISK = ["Requested large wire transfer to external institution","Declined renewal offer on maturing CD",
    "Asked about account closure process"]
NOTES_HEALTHY = ["Routine balance inquiry","Updated contact information","Discussed investment options",
    "Satisfied with current rate","Positive interaction - interested in new products"]

risk_data = []
snapshot_date = (TODAY - timedelta(days=1)).isoformat()
for cust in customer_data:
    cid, _, tier, tenure, _, _, _, _ = cust
    cust_idx = int(cid.split("-")[1])
    if cust_idx % 37 == 0 and tier in ("affluent", "private"):
        risk_score = round(random.uniform(0.75, 0.92), 4)
        outflow = round(random.uniform(5000, 50000), 2)
        note = random.choice(NOTES_CHURN)
    elif cust_idx % 111 == 0 and tier in ("affluent", "private", "mass_affluent"):
        risk_score = round(random.uniform(0.60, 0.74), 4)
        outflow = round(random.uniform(2000, 15000), 2)
        note = random.choice(NOTES_ATRISK)
    elif cust_idx % 400 == 0:
        risk_score = round(random.uniform(0.40, 0.59), 4)
        outflow = round(random.uniform(500, 5000), 2)
        note = random.choice(NOTES_ATRISK + NOTES_HEALTHY)
    else:
        risk_score = round(random.uniform(0.02, 0.25), 4)
        outflow = round(random.uniform(0, 500), 2)
        note = random.choice(NOTES_HEALTHY)
    risk_data.append((cid, snapshot_date, risk_score, outflow, note))

# Historical snapshots for time-series richness
for days_back in [7, 14, 21]:
    hist_date = (TODAY - timedelta(days=days_back + 1)).isoformat()
    for cust in random.sample(customer_data, 1000):
        risk_data.append((cust[0], hist_date, round(random.uniform(0.02,0.30),4), round(random.uniform(0,1000),2), random.choice(NOTES_HEALTHY)))

risk_df = spark.createDataFrame(risk_data, schema=StructType([
    StructField("customer_id", StringType()), StructField("snapshot_date", StringType()),
    StructField("attrition_risk_score", DoubleType()), StructField("balance_outflow_30d_usd", DoubleType()),
    StructField("servicing_note_text", StringType()),
]))
risk_df.write.mode("overwrite").parquet(f"{VOLUME_PATH}/risk_snapshots")
print(f"risk_snapshots: {risk_df.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Retention Campaigns (~35K)

# COMMAND ----------

random.seed(46)
campaign_data = []
for i in range(35000):
    cid = f"CUST-{random.randint(0, 39999):07d}"
    cust = next((c for c in customer_data if c[0] == cid), None)
    tier = cust[2] if cust else random.choice(TIERS)
    pid = random.choice(AFFECTED_PRODUCTS + ["PROD-DEP-1001", "PROD-DEP-1002"])
    action = random.choice(["retention_offer", "cross_sell", "rm_outreach"])
    balance = round(random.uniform(10000, 800000) if tier in ("affluent","private") else random.uniform(5000, 100000), 2)
    risk_at_action = round(random.uniform(0.4, 0.9), 4)
    initiated = (TODAY - timedelta(days=random.randint(30, 365))).isoformat()
    days_resolve = random.randint(1, 30)
    if action == "retention_offer" and risk_at_action > 0.6:
        retained = 1 if random.random() < 0.7 else 0
        retained_rev = round(balance * 0.025 * random.uniform(1.5, 3.5), 2) if retained else 0
    elif action == "cross_sell":
        retained = 1 if random.random() < 0.5 else 0
        retained_rev = round(balance * 0.015 * random.uniform(1.0, 2.5) + 1200, 2) if retained else 0
    else:
        retained = 1 if random.random() < 0.4 else 0
        retained_rev = round(balance * 0.01 * random.uniform(1.0, 2.0), 2) if retained else 0
    margin_impact = round(retained_rev * random.uniform(0.05, 0.15), 2) if retained else 0
    cost = round(balance * random.uniform(0.001, 0.005), 2) if action == "retention_offer" else round(random.uniform(20, 100), 2)
    offered_pid = random.choice(["PROD-INV-3001","PROD-CRD-4001","PROD-LN-5001"]) if action == "cross_sell" else None
    campaign_data.append((f"CAMP-{i:07d}", cid, pid, action, offered_pid, balance, risk_at_action, initiated, days_resolve, retained, retained_rev, margin_impact, cost))

campaign_df = spark.createDataFrame(campaign_data, schema=StructType([
    StructField("campaign_id", StringType()), StructField("customer_id", StringType()),
    StructField("product_id", StringType()), StructField("action_type", StringType()),
    StructField("offered_product_id", StringType()), StructField("balance_at_risk_usd", DoubleType()),
    StructField("attrition_risk_at_action", DoubleType()), StructField("initiated_date", StringType()),
    StructField("days_to_resolve", IntegerType()), StructField("retained", IntegerType()),
    StructField("retained_revenue_usd", DoubleType()), StructField("margin_impact_usd", DoubleType()),
    StructField("cost_usd", DoubleType()),
]))
campaign_df.write.mode("overwrite").parquet(f"{VOLUME_PATH}/retention_campaigns")
print(f"retention_campaigns: {campaign_df.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n=== Data Generation Complete ===")
for ds in ["customers", "products", "holdings", "transactions", "risk_snapshots", "retention_campaigns"]:
    df = spark.read.parquet(f"{VOLUME_PATH}/{ds}")
    print(f"  {ds}: {df.count():,} rows")
