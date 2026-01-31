# Databricks in a Nutshell

**A hands-on introduction to Databricks for beginner Data Engineers.**

This project is a step-by-step guide: from “what is Databricks” to a working Bronze → Gold pipeline with a table in Unity Catalog and Power BI connectivity.

---

## Table of Contents

1. [What is Databricks](#1-what-is-databricks)
2. [What Databricks Works With](#2-what-databricks-works-with)
3. [Why Databricks is Useful](#3-why-databricks-is-useful)
4. [Apache Spark and PySpark in Brief](#4-apache-spark-and-pyspark-in-brief)
5. [Workspace Creation and Networking](#5-workspace-creation-and-networking)
6. [Logging into the Workspace. Clusters](#6-logging-into-the-workspace-clusters)
7. [Serverless and Cluster Types in Production](#7-serverless-and-cluster-types-in-production)
8. [Notebooks, Jobs, and Schedules](#8-notebooks-jobs-and-schedules)
9. [Storage: DBFS and Storage Types](#9-storage-dbfs-and-storage-types)
10. [Practice: Bronze → Gold Pipeline](#10-practice-bronze--gold-pipeline)
11. [Unity Catalog and Tables](#11-unity-catalog-and-tables)
12. [Connecting Power BI](#12-connecting-power-bi)
13. [GitHub and Databricks Repos](#13-github-and-databricks-repos)

---

## 1. What is Databricks

**Databricks** is a cloud platform for data and ML built on **Apache Spark**.

- It is **compute**, not storage: data can live in S3, ADLS, GCS, or DBFS.
- Databricks provides: Workspace (notebooks, jobs, MLflow), cluster management, Unity Catalog, and integrations with clouds (AWS, Azure, GCP).
- The idea: one product for ETL, analytics, ML, and collaboration.

---

## 2. What Databricks Works With

| Component | Role |
|-----------|------|
| **AWS / Azure / GCP** | Infrastructure: VPC, storage (S3, ADLS, etc.), IAM |
| **Apache Spark** | Distributed compute engine |
| **Delta Lake** | Table format on top of Parquet with ACID and time travel |
| **Unity Catalog** | Unified metadata catalog, access control, lineage |
| **DBFS** | Workspace’s internal file storage (Managed Storage) |
| **GitHub / Git** | Code versioning, CI/CD |

---

## 3. Why Databricks is Useful

- **Single platform**: ETL, streaming, ML, SQL, BI — without juggling multiple tools.
- **Scale**: Spark scales across nodes; you can size the cluster to the workload.
- **Cluster management**: auto start/stop, serverless — less manual tuning.
- **Unity Catalog**: one catalog for tables and permissions across the organization.
- **Cloud integration**: native S3/ADLS, IAM, private networking.

---

## 4. Apache Spark and PySpark in Brief

- **Apache Spark** — a framework for distributed processing of large data (batch and streaming).
- **RDD / DataFrame / Dataset** — data abstractions; in day-to-day work you mostly use **DataFrame** (tables).
- **PySpark** — Spark API in Python: `spark.read`, `df.write`, SQL via `spark.sql()`.

Example:

```python
df = spark.read.json("/path/to/file.json")
df.write.mode("overwrite").parquet("/path/to/output")
```

Spark distributes data across cluster nodes — no need to write multi-threaded code yourself.

---

## 5. Workspace Creation and Networking

The Workspace is created in the cloud console (AWS/Azure) or via the Databricks partner portal. It’s important to know **where** this Databricks will “point” — that drives network and data access.

### Why Networking Matters

- Databricks clusters must **reach** storage (S3, ADLS, internal DBs) and your network (VPN, VPC).
- Network setup affects: security, privacy, and compliance with corporate policies.

### By Cloud

| Cloud | What to Configure |
|-------|-------------------|
| **AWS** | VPC, subnets, security groups; S3 endpoint or NAT for internet; optionally PrivateLink / VPC endpoint for Databricks. |
| **Azure** | VNet, subnets, Private Endpoints to ADLS and Databricks; optionally Secure Cluster Connectivity (no public IP). |
| **GCP** | VPC, firewall; optionally Private Service Connect. |

Recommendation: for production use **private** options (PrivateLink, Secure Cluster Connectivity) so traffic doesn’t go over the public internet.

Details: [AWS](https://docs.databricks.com/administration-guide/cloud-configurations/aws/index.html), [Azure](https://docs.databricks.com/administration-guide/cloud-configurations/azure/index.html).

---

## 6. Logging into the Workspace. Clusters

After creating the Workspace, open a URL like `https://<workspace>.cloud.databricks.com` (or Azure/GCP domain). Log in via SSO or email/password, depending on your org’s settings.

### What is a Cluster

A **cluster** in Databricks is a set of VMs (driver + workers) that run Spark.

- **Driver** — one node: coordinates tasks, holds session metadata.
- **Workers** — nodes that run the actual work. More workers / more cores and memory → heavier workloads.

Without a cluster you cannot run any notebook cell or Job.

### Cluster Types

| Type | Description |
|------|-------------|
| **All-purpose (Interactive)** | For interactive work: notebooks, ad-hoc queries. Stays up until you stop it (or timeout). |
| **Job** | Started for a specific Job and terminates when the Job finishes. Saves cost. |
| **Pool (Cluster pool)** | A pool of “warm” nodes; Job clusters from the pool start faster than from scratch. |

For when to use which in production, see [Section 7](#7-serverless-and-cluster-types-in-production).

---

## 7. Serverless and Cluster Types in Production

You can use **Serverless** (where available): the cluster is not “your” set of VMs but an abstraction — Databricks allocates and releases resources.

### When to Use What

| Scenario | Recommendation |
|----------|----------------|
| **Development, experimentation** | All-purpose cluster (or Serverless SQL/notebooks if enabled). |
| **Production: predictable Jobs** | **Job cluster** (or **Serverless Jobs**) — start, run, shut down. |
| **Production: many short Jobs** | **Serverless** or **Cluster pool** + Job clusters from the pool — less cold start. |
| **Production: strict resource control** | **Dedicated Job clusters** with fixed instance types. |
| **Production: SQL Warehouse / BI** | **Serverless SQL** (if available) — no need to keep a cluster for dashboards. |

Summary for production:

- **Dedicated / Job clusters** — when you need predictable instances and isolation.
- **Serverless** — when you want simplicity and fast startup without managing nodes.
- **Cluster pool** — when you have many Jobs and care about startup time (reusing warm nodes).

**Serverless Workspace** (if you have that option): a Workspace where some compute is serverless by default (e.g. SQL Warehouses and sometimes Jobs). Good for teams that want less infra to manage; for heavy or special workloads you can still use regular clusters.

---

## 8. Notebooks, Jobs, and Schedules

- **Notebook** — interactive environment (code cells, markdown). Runs on a chosen cluster. Good for development and debugging.
- **Job** — a task that runs one or more notebooks/scripts (or JAR) **non-interactively**. Trigger: manual or **schedule** (cron).
- **Schedule** — in the Job settings you set a schedule (e.g. daily at 02:00). This is how production pipelines are usually run.

Practice: develop in a notebook → turn it into a Job → add a schedule.

---

## 9. Storage: DBFS and Storage Types

### DBFS (Databricks File System)

**DBFS** is a file-system abstraction that your Workspace sees. It sits on top of cloud storage.

- In many setups, the DBFS root is backed by **Managed Storage** — storage that Databricks creates and manages for that Workspace (e.g. an S3 bucket or ADLS container).
- Paths like `/FileStore/`, the root for user data, etc. are DBFS. In the UI: **Data** → **Add** → **Upload data** or folder browsing — that’s this storage (you can add a screenshot: Data → data management / Upload — “this is the Managed Data Storage created by the Workspace”).

### Storage Types

| Type | Description |
|------|-------------|
| **Managed (DBFS root / FileStore)** | Created and managed by Databricks. Convenient for artifacts, small files, demos. |
| **External / Customer-managed** | Your S3 bucket / ADLS container. You control lifecycle and access. Production data often lives here. |
| **Unity Catalog Volumes** | Folders inside a UC catalog for files (e.g. for ML and shared datasets). |

In the practice section we put JSON in this storage (e.g. a folder in DBFS/Managed), then read it from a notebook and write Bronze/Gold.

---

## 10. Practice: Bronze → Gold Pipeline

Short scenario:

1. **Setup**
   - Take any small JSON file.
   - Upload it to DBFS (e.g. `/FileStore/bronze/input/sample.json` or your folder in Managed storage). Along the way: “this is our Workspace’s internal storage (DBFS / Managed).”

2. **Bronze**
   - Create a notebook (PySpark).
   - Read JSON: `spark.read.json("dbfs:/path/to/sample.json")`.
   - Save to a **bronze** folder as Parquet (or Delta): e.g. `.../bronze/events/`.

3. **Gold**
   - Create a second notebook.
   - Read Parquet from bronze: `spark.read.parquet("dbfs:/.../bronze/events/")`.
   - Optionally: filter, rename, aggregate.
   - Write to **gold**: `.../gold/events/`.

4. **Table and Unity Catalog**
   - In gold, create a table (Delta) and **register it in Unity Catalog** (external or managed table) so Power BI and other tools can connect to it.

Step-by-step and code samples: [PRACTICE.md](PRACTICE.md).

---

## 11. Unity Catalog and Tables

- **Unity Catalog (UC)** — unified metadata catalog: schemas, tables, views, permissions (GRANT/REVOKE).
- We **register** the gold table in UC (`CREATE TABLE ... USING delta LOCATION '...'` or `CREATE TABLE ... AS SELECT ...`).
- After that, the table is accessed by three-level name: `catalog.schema.table`. That’s what Power BI connects to.

---

## 12. Connecting Power BI

- In Power BI: **Get data** → **Azure Databricks** (or **Databricks**).
- Enter **Server hostname** (Workspace URL), **HTTP path** (from cluster or SQL Warehouse), and authentication (usually Personal Access Token or OAuth).
- Choose **Unity Catalog** (or legacy Hive metastore): catalog, schema, gold table.
- Build a report on that table.

For production, use a **SQL Warehouse** (including Serverless) as the BI entry point, not an interactive cluster.

---

## 13. GitHub and Databricks Repos

Code should live in **GitHub** (or another Git), and in Databricks connect via **Repos**.

- **User Settings** → **Git Integration** → connect GitHub (token with `repo` scope).
- In the Workspace: **Repos** → **Add Repo** → repository URL. Develop notebooks and scripts in the repo (or sync with it).
- Jobs should run from the `main` branch so production always uses a committed version.

Result: single source of truth for code (GitHub), versioning, code review, and safe deployments.

---

## Project Architecture (Summary)

```
GitHub (code)
    ↓ Repos
Databricks Workspace
    ↓ Jobs / Notebooks
DBFS / External Storage (Bronze → Gold)
    ↓
Unity Catalog (tables)
    ↓
Power BI (and other BI tools)
```

---

## Repository Structure

```
Databricks-Project-Sa/
├── README.md                 # this guide
├── PRACTICE.md               # step-by-step Bronze → Gold practice
├── notebooks/
│   ├── 01_bronze_ingest.py   # read JSON → write to bronze (Parquet/Delta)
│   └── 02_gold_transform.py  # read bronze → write to gold + UC table
├── data/
│   └── sample.json           # sample JSON to upload to DBFS
└── jobs/
    └── daily_pipeline.json   # example Job config (optional)
```

---

## What You’ll Get After Completing

- Understanding: what Databricks is, Spark/PySpark, Workspace, clusters, serverless.
- Awareness of networking when deploying (AWS/Azure).
- Hands-on: upload to DBFS, Bronze → Gold notebooks, table in Unity Catalog, Power BI connection.
- Working with code via GitHub and Databricks Repos.

If you want to expand any section into a separate file (e.g. networking or clusters only), you can move it to `docs/` and link from this README.
