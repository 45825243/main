# Databricks notebook source
# MAGIC %md
# MAGIC ## Bronze: Ingest JSON to Parquet
# MAGIC Read JSON from DBFS (folder where you uploaded sample.json) and save to the Bronze folder as Parquet.

# COMMAND ----------

# Path to JSON in DBFS (replace with your path after uploading via Data → Upload)
input_path = "/FileStore/bronze/input/sample.json"
bronze_path = "/FileStore/bronze/events"

# COMMAND ----------

df = spark.read.json(input_path)
df.printSchema()

# COMMAND ----------

# Optional: view query plan and physical plan (see README — Query plan and physical plan)
df.explain("formatted")

# COMMAND ----------

df.show(10)

# COMMAND ----------

# Write to Bronze as Parquet
df.write.mode("overwrite").format("parquet").save(bronze_path)

# COMMAND ----------

# Verify: read back from Bronze
spark.read.parquet(bronze_path).show(5)
