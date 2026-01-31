# Practice: Bronze → Gold in Databricks

Step-by-step pipeline: upload JSON to DBFS, read in a notebook, write to Bronze and Gold, register the table in Unity Catalog.

---

## Prerequisites

- A Databricks Workspace (AWS or Azure).
- A cluster with a supported runtime (e.g. 14.3 LTS) in **Running** state.
- Permission to create catalog/schema in Unity Catalog (or use default `main` / legacy Hive).

---

## Step 1. Upload JSON to DBFS

1. Prepare a small JSON file (e.g. `data/sample.json` from the repo).
2. In the Workspace use **New** → **Data** (or **Create** → **Data**), then **DBFS** or **Upload files to volume**; or from a notebook **File** → **Add data**. (Exact labels may vary by version; see [docs](https://docs.databricks.com/en/ingestion/add-data/index.html) if you don’t see these.)
3. Create a folder for input, e.g. `bronze/input/`.
4. Upload the file into that folder (via UI or CLI).

The path in DBFS will look like:
- `dbfs:/FileStore/bronze/input/sample.json` (if uploaded to FileStore), or
- `dbfs:/Volumes/<catalog>/<schema>/<volume>/bronze/input/sample.json` (if using Volumes).

**Note:** This is the Workspace’s “internal” storage — DBFS. Managed Data Storage is created for the Workspace; in the UI you are managing this storage (you can add a screenshot of Data / Upload).

---

## Step 2. Bronze Notebook: Read JSON and Write to Bronze

1. Create a new **Notebook** (or open from Repo `notebooks/01_bronze_ingest.py`).
2. Attach the notebook to a cluster.
3. In the first cell set the path to your JSON (replace with your path):

```python
# Path to JSON in DBFS (replace after uploading via Data → Upload)
input_path = "/FileStore/bronze/input/sample.json"
bronze_path = "/FileStore/bronze/events"
```

4. Read JSON and write to Bronze as Parquet:

```python
df = spark.read.json(input_path)
df.write.mode("overwrite").format("parquet").save(bronze_path)
```

5. **(Optional) View query plan and physical plan:**  
   Before or after the write, you can inspect how Spark will execute (or has executed) the read/write. Run one of the following on a DataFrame (e.g. the one you built with `spark.read.json` or the one you get from `spark.read.parquet`):

```python
# Logical plan only
df.explain(mode="simple")

# Logical + physical plan (extended)
df.explain(mode="extended")

# Formatted output (easy to read in notebooks)
df.explain("formatted")
```

   This shows the logical operators (e.g. Read, Filter) and the physical plan (FileScan, Exchange, etc.). See [README — Query plan and physical plan](README.md#query-plan-and-physical-plan) for more detail.

6. Verify:

```python
spark.read.parquet(bronze_path).show(5)
```

Save the notebook. The folder `bronze/events` now contains data in Parquet format.

---

## Step 3. Gold Notebook: Read Parquet from Bronze and Write to Gold

1. Create a second notebook (or open `notebooks/02_gold_transform.py`).
2. Attach it to the same cluster (or another one).
3. Set paths:

```python
bronze_path = "/FileStore/bronze/events"
gold_path = "/FileStore/gold/events"
```

4. Read from Bronze, minimal processing, write to Gold (Delta is recommended for tables):

```python
df = spark.read.parquet(bronze_path)
# Optionally: filter, rename columns, add columns
# df = df.filter(...).select(...)
df.write.mode("overwrite").format("delta").save(gold_path)
```

5. **(Optional) View query plan and physical plan:**  
   After building `df` (e.g. `df = spark.read.parquet(bronze_path)`), run `df.explain("formatted")` to see the logical and physical plan for the read. If you add filters or joins, run `explain` on the transformed DataFrame to see pushdown and join strategy.

6. Verify:

```python
spark.read.format("delta").load(gold_path).show(5)
```

---

## Step 4. Register the Table in Unity Catalog

In the same Gold notebook (or a new SQL/Python notebook) create a table on the Gold path and register it in Unity Catalog.

**Option A — external table:**

```sql
CREATE TABLE IF NOT EXISTS main.default.gold_events
USING DELTA
LOCATION '/FileStore/gold/events';
```

Replace `main.default` with your `catalog.schema` if not using default.

**Option B — from Python:**

```python
spark.sql("""
  CREATE TABLE IF NOT EXISTS main.default.gold_events
  USING DELTA
  LOCATION '/FileStore/gold/events'
""")
```

The table `main.default.gold_events` (or your `catalog.schema.table`) is now in Unity Catalog — you can build reports in Power BI and manage access via UC.

---

## Step 5. Connect Power BI to the Table

1. In Power BI: **Get data** → **Azure Databricks** (or **Databricks**).
2. Enter:
   - **Server:** `https://<workspace>.cloud.databricks.com` (or Azure URL).
   - **HTTP Path:** from the cluster (Advanced options → JDBC/ODBC) or from the SQL Warehouse.
   - **Authentication:** Personal Access Token or OAuth.
3. In the navigator select **Unity Catalog** (if using it) and the table `main.default.gold_events` (or your catalog.schema.table).
4. Load the data and build your report.

For production, connect Power BI to a **SQL Warehouse** (including Serverless) rather than an interactive cluster.

---

## Step 6. Job and Schedule (Optional)

1. In the Workspace: **Workflows** → **Jobs** → **Create Job**.
2. Add a task: run notebook `01_bronze_ingest`.
3. Add a second task: run notebook `02_gold_transform` (depends on the first).
4. In the Job settings choose a **Job cluster** (or Serverless if available).
5. Under **Schedule** set a schedule (e.g. daily at 02:00).

The Bronze → Gold pipeline will then run on a schedule without manual runs.

---

## Summary

- JSON is uploaded to DBFS (Workspace’s internal/Managed storage).
- Bronze notebook reads JSON and writes Parquet to `bronze/events`.
- Gold notebook reads Parquet from Bronze and writes Delta to `gold/events`.
- The table is registered in Unity Catalog.
- Power BI connects to that table.
- Optionally, the pipeline is defined as a Job with a schedule.

For real projects, put paths in config or environment variables and keep code in GitHub with Databricks Repos.
