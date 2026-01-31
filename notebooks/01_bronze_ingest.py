# Databricks notebook source
# MAGIC %md
# MAGIC ## Bronze: Ingest JSON to Parquet
# MAGIC Read JSON from Unity Catalog Volume firstdbfs_surfaltics and save to Bronze folder as Parquet.

# COMMAND ----------

# Paths in Unity Catalog Volume firstdbfs_surfaltics (workspace.default)
input_path = "/Volumes/workspace/default/firstdbfs_surfaltics/sample.json"
bronze_path = "/Volumes/workspace/default/firstdbfs_surfaltics/bronze/events"

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
