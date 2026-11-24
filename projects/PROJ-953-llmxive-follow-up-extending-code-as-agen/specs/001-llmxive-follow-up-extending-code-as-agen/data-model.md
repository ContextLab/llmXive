# Data Model: llmXive Harness Extension

## Data Flow Overview

The pipeline processes software‑engineering tasks through three main phases:

1. **Ingestion** – Raw tasks are fetched from HuggingFace (SWE‑bench and AgentBench), parsed, and stored as Parquet files. A dynamic execution baseline is run to produce ground‑truth outcomes.
2. **Feature Extraction** – Code diffs are parsed with `tree‑sitter` to generate dependency graphs and compute structural metrics (dependency depth, cyclomatic complexity, semantic complexity, lines of code, etc.).
3. **Modeling** – Features are merged with ground‑truth labels, models are trained, and a sensitivity analysis sweeps decision thresholds to identify safe static‑analysis boundaries.

The high‑level data flow can be visualised as:

```mermaid
graph TD
    A[Raw Datasets: SWE‑bench / AgentBench] -->|ingest.py| B[data/raw/*.parquet]
    B -->|baseline_runner.py| C[data/processed/raw_outcomes.json]
    C -->|generate_ground_truth.py| D[data/processed/ground_truth.csv]
    D -->|extract_features.py| E[data/graphs/{task_id}.json]
    D -->|extract_features.py| F[data/processed/features.csv]
    F -->|train_model.py| G[models/*.pkl]
    G -->|train_model.py| H[data/processed/threshold_sweep.json]
    G -->|train_model.py| I[data/processed/model_report.json]
```

## Directory Structure & Artifacts

The project adheres to a strict directory convention:

- `data/raw/` – Immutable raw ingested Parquet files and initial CSV logs.  
- `data/processed/` – Cleaned, merged CSV/JSON artifacts (ground truth, features, model reports, threshold sweeps).  
- `data/graphs/` – Serialized dependency graphs for each task (`{task_id}.json`).  
- `data/logs/` – Execution logs, sampling justifications, and audit reports.  
- `models/` – Pickled model artifacts (`logistic_regression.pkl`, `random_forest.pkl`).  
- `contracts/` – JSON‑Schema definitions governing the shape of all artifacts.  
- `specs/001-llmxive-follow-up-extending-code-as-agen/` – Specification documents, including this data‑model description.  

## Schema Definitions

All data artifacts must conform to the schemas located in `contracts/`:

- **`task_artifact.schema.yaml`** – Defines the raw task records before ground‑truth generation.  
- **`structural_metric.schema.yaml`** – Defines the feature records produced by `extract_features.py`.  
- **`model_outcome.schema.yaml`** – Defines the model‑training outputs (`threshold_sweep.json`, `model_report.json`).  

These schemas are enforced via `jsonschema` validation in the pipeline scripts and unit tests.

## Artifact Relationships

1. **Ground‑Truth Generation**  
   - **Inputs:** `data/raw/swe_bench_subset.parquet`, `data/raw/agentbench_subset.parquet`  
   - **Process:** `scripts/baseline_runner.py` executes each task in an isolated environment.  
   - **Intermediate:** `data/processed/raw_outcomes.json` (execution outcomes).  
   - **Output:** `data/processed/ground_truth.csv` containing `task_id`, `code_diff`, `status`, and `dynamic_execution_outcome`.  

2. **Feature Extraction**  
   - **Input:** `data/processed/ground_truth.csv` (filtered to exclude rows where `status="Unparseable"`).  
   - **Process:** `scripts/extract_features.py` parses `code_diff` with `tree‑sitter`, builds a dependency graph, and computes metrics.  
   - **Outputs:**  
     - `data/graphs/{task_id}.json` – Serialized graph per task.  
     - `data/processed/features.csv` – Merged feature table adhering to `structural_metric.schema.yaml`.  

3. **Modeling & Reporting**  
   - **Input:** `data/processed/features.csv`.  
   - **Process:** `scripts/train_model.py` trains Logistic Regression and Random Forest models, performs a threshold sweep, and calculates Pearson correlations.  
   - **Outputs:**  
     - `models/logistic_regression.pkl`, `models/random_forest.pkl` – Serialized models.  
     - `data/processed/threshold_sweep.json` – FNR values for thresholds `{0.01, 0.05, 0.1}`.  
     - `data/processed/model_report.json` – Consolidated report containing `framing: "associational"` and safety flags, validated against `model_outcome.schema.yaml`.  

Together, these artifacts form a reproducible, contract‑driven pipeline that links raw agent tasks to predictive models of verification necessity.