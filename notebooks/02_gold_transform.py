# Databricks notebook source
# MAGIC %md
# MAGIC ## Gold: Read from Bronze (Parquet) and Write to Gold (Delta)
# MAGIC Register the table in Unity Catalog for access from Power BI and other tools.

# COMMAND ----------

bronze_path = "/FileStore/bronze/events"
gold_path = "/FileStore/gold/events"

# COMMAND ----------

# Read Parquet from Bronze
df = spark.read.parquet(bronze_path)
df.printSchema()

# COMMAND ----------

# Optional: view query plan and physical plan (see README — Query plan and physical plan)
df.explain("formatted")

# COMMAND ----------

# Minimal processing (optionally: filters, rename, aggregations)
# df = df.filter(...).select(...)
# For this demo we simply overwrite to Gold as Delta
df.write.mode("overwrite").format("delta").save(gold_path)

# COMMAND ----------

# Verify
spark.read.format("delta").load(gold_path).show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Table in Unity Catalog
# MAGIC Replace `main.default` with your catalog.schema if not using default.

# COMMAND ----------

spark.sql("""
  CREATE TABLE IF NOT EXISTS main.default.gold_events
  USING DELTA
  LOCATION '/FileStore/gold/events'
""")

# COMMAND ----------

# Verify: table is accessible via UC
spark.table("main.default.gold_events").show(5)
