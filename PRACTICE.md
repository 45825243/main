# Practice: Bronze → Gold in Databricks

Step-by-step pipeline: upload JSON to DBFS, read in a notebook, write to Bronze and Gold, register the table in Unity Catalog.

---

## Prerequisites

- A Databricks Workspace (AWS or Azure).
- A cluster with a supported runtime (e.g. 14.3 LTS) in **Running** state.
- Permission to create catalog/schema in Unity Catalog (or use default `main` / legacy Hive).

---

## Concepts: Unity Catalog and Delta tables

Before you start, two things you’ll use in this practice:

**Unity Catalog (UC)** — a unified governance layer for data and AI in Databricks. It gives you a single place for metadata: catalogs, schemas, tables, views, and permissions (GRANT/REVOKE). Tables are addressed as `catalog.schema.table`. UC works with Delta tables and with cloud storage (S3, ADLS) via external locations. In this practice we use a **Unity Catalog Volume** (a folder for files under UC) for Bronze/Gold data and register a table in UC so Power BI (and other tools) can query it.

**Delta tables** — tables whose data is stored in the **Delta Lake** format (Parquet files plus a transaction log). Delta gives you ACID transactions, time travel, and efficient upserts/merges. In this practice we write the Gold layer as Delta (`df.write.format("delta").save(...)`) and then register it in Unity Catalog. Delta is the default and recommended format for tables in Databricks.

---

## Step 1. Upload JSON to a Unity Catalog Volume

We use the Unity Catalog Volume **`firstdbfs_surfaltics`** in catalog `workspace`, schema `default`. Path: **`/Volumes/workspace/default/firstdbfs_surfaltics`**.

1. Prepare a small JSON file (e.g. `data/sample.json` from the repo).
2. In the Workspace open **Catalog** → your catalog (e.g. **workspace**) → **Volumes** → open the volume **firstdbfs_surfaltics** (or create it: **Create** → **Volume** in the schema `default`).
3. Upload the file into the volume (e.g. drag-and-drop or **Upload file**). Put `sample.json` at the root of the volume or in a subfolder (e.g. `bronze/input/`).

**Paths used in this practice:**

| What | Path |
|------|------|
| Volume root | `/Volumes/workspace/default/firstdbfs_surfaltics` |
| Input JSON | `/Volumes/workspace/default/firstdbfs_surfaltics/sample.json` (or `.../bronze/input/sample.json` if you use a subfolder) |
| Bronze (Parquet) | `/Volumes/workspace/default/firstdbfs_surfaltics/bronze/events` |
| Gold (Delta) | `/Volumes/workspace/default/firstdbfs_surfaltics/gold/events` |

**Note:** Unity Catalog Volumes live in DBFS under `/Volumes/<catalog>/<schema>/<volume>/`. Your data stays in the volume; Bronze and Gold folders will be created by the notebooks inside this volume.

---

## Step 2. Bronze Notebook: Read JSON and Write to Bronze

1. Create a new **Notebook** (or open from Repo `notebooks/01_bronze_ingest.py`).
2. Attach the notebook to a cluster.
3. In the first cell set the paths (Volume `firstdbfs_surfaltics`):

```python
# Paths in Unity Catalog Volume firstdbfs_surfaltics (workspace.default)
input_path = "/Volumes/workspace/default/firstdbfs_surfaltics/sample.json"
bronze_path = "/Volumes/workspace/default/firstdbfs_surfaltics/bronze/events"
```
If you uploaded `sample.json` into a subfolder (e.g. `bronze/input/`), set `input_path` to `/Volumes/workspace/default/firstdbfs_surfaltics/bronze/input/sample.json`.

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
3. Set paths (same Volume):

```python
bronze_path = "/Volumes/workspace/default/firstdbfs_surfaltics/bronze/events"
gold_path = "/Volumes/workspace/default/firstdbfs_surfaltics/gold/events"
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

Unity Catalog **does not** allow `CREATE TABLE ... LOCATION` pointing to a path inside a Volume (or using the `dbfs:` scheme). You get: *"Creating table in Unity Catalog with file scheme dbfs is not supported"*. Tables and Volumes cannot overlap.

**Use a managed table** created from the Delta data in the Volume (data is stored in the catalog’s managed storage):

**Option A — SQL (managed table):**

```sql
CREATE OR REPLACE TABLE workspace.default.gold_events
AS SELECT * FROM delta.`/Volumes/workspace/default/firstdbfs_surfaltics/gold/events`;
```

Replace `workspace.default` with your `catalog.schema` if different.

**Option B — from Python:**

```python
spark.sql("""
  CREATE OR REPLACE TABLE workspace.default.gold_events
  AS SELECT * FROM delta.`/Volumes/workspace/default/firstdbfs_surfaltics/gold/events`
""")
```

The table `workspace.default.gold_events` is now in Unity Catalog (managed table). You can build reports in Power BI and manage access via UC. The Delta files in the Volume remain; the table is a copy in the catalog’s managed storage.

**Alternative:** If you want an **external** table (data stays in one place), write Gold to an **external location** (S3/ADLS path registered in UC), then `CREATE TABLE ... USING DELTA LOCATION 's3://bucket/path'` (cloud URI, not Volume path).

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

- JSON is uploaded to the Unity Catalog Volume `/Volumes/workspace/default/firstdbfs_surfaltics`.
- Bronze notebook reads JSON and writes Parquet to `.../firstdbfs_surfaltics/bronze/events`.
- Gold notebook reads Parquet from Bronze and writes Delta to `.../firstdbfs_surfaltics/gold/events`.
- The table is registered in Unity Catalog.
- Power BI connects to that table.
- Optionally, the pipeline is defined as a Job with a schedule.

For real projects, put paths in config or environment variables and keep code in GitHub with Databricks Repos.
