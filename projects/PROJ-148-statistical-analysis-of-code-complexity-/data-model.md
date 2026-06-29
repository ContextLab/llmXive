# Data‑Model Design Document
*Statistical Analysis of Code Complexity Metrics and Bug Prediction*
(Project **PROJ‑148**)

**Version:** 1.0 – 2026‑06‑29
**Author:** LLM‑Xive Implementer

## 1. Overview

This document describes the canonical data model used throughout the project.
It defines the raw and processed datasets that feed the statistical‑modeling
pipeline, the relationships between entities (projects, commits, source files,
and metric observations), and the schema contracts that enforce data quality.

The design adheres to the contracts created in earlier tasks:

* **Dataset contract:** `contracts/dataset.schema.yaml`
* **Model output contract:** `contracts/model_output.schema.yaml`

The data model is deliberately **flat** for the machine‑learning stage (one
observation per source code unit) while preserving hierarchical identifiers
(project, commit, file) for downstream analysis and reproducibility.

## 2. Core Entities

| Entity | Description | Primary Key |
|--------|-------------|-------------|
| **Project** | A Java open‑source repository obtained from GHTorrent. | `project_id` (string, e.g., `apache/commons-lang`) |
| **Commit** | A Git commit within a project that introduced a source file version. | `commit_sha` (string, 40‑char SHA‑1) |
| **File** | A Java source file (`*.java`) at a specific commit. | `file_path` (string, relative to repo root) |
| **MetricObservation** | A single row of extracted complexity metrics for a file version, together with the bug‑fix label. | Composite key: (`project_id`, `commit_sha`, `file_path`) |

## 3. Processed Dataset Schema

The processed, model‑ready dataset is stored as **Parquet** at
`data/processed/dataset.parquet`. Its schema is defined by the JSON‑Schema
contract `contracts/dataset.schema.yaml`. The following table mirrors that
contract and adds human‑readable descriptions.

| Column | Type | Description |
|--------|------|-------------|
| `project_id` | string | Unique identifier of the GitHub project (`owner/repo`). |
| `commit_sha` | string | SHA‑1 hash of the commit that introduced the file version. |
| `file_path` | string | Path of the Java source file inside the repository. |
| `loc` | int | **Lines of Code** – total non‑blank, non‑comment lines. |
| `cyclomatic_complexity` | float | Average cyclomatic complexity per function (computed by *lizard*). |
| `token_count` | int | Number of lexical tokens in the file. |
| `nesting_depth` | float | Mean nesting depth of control structures. |
| `halstead_volume` | float | Halstead Volume metric (size of implementation). |
| `num_functions` | int | Number of function/method definitions detected. |
| `bug_label` | int (0/1) | Binary target: `1` if the commit is a bug‑fix (determined from issue linking & commit message heuristics), otherwise `0`. |
| `author_date` | datetime | Timestamp of the commit author date (UTC). |
| `is_test_file` | bool | Heuristic flag (`true` if path contains `test` or filename ends with `Test.java`). |
| `project_language` | string | Primary language of the project (always `Java` for this study). |
| `split` | string (`train`/`test`) | Stratified split assignment (project‑level, 70 % train / 30 % test). [UNRESOLVED-CLAIM: c_801e85f9 — status=not_enough_info] |

### 3.1 Derived Features (added in later preprocessing steps)

* `log_loc`, `log_token_count`, `log_halstead_volume` – {{claim:c_85e95373}}
* `missing_indicator_<metric>` – Boolean flags for imputed values (used when < 5 % missing). [UNRESOLVED-CLAIM: c_1bf07c69 — status=refuted]

These columns are **not** part of the contract but are persisted in the same
Parquet file for convenience.

## 4. Model Output Schema

Model predictions and evaluation results are stored under `data/model/` and
must conform to `contracts/model_output.schema.yaml`. The key fields are:

* `prediction_id` – UUID for the prediction row.
* `project_id`, `commit_sha`, `file_path` – foreign keys back to the original observation.
* `probability_bug` – Predicted probability (float ∈ [0, 1]).
* `predicted_label` – Binary label obtained by thresholding at 0.5.
* `model_version` – Semantic version of the model that generated the prediction.

## 5. Data Lineage & Versioning

1. **Raw download** – `code/data/download_gh.py` fetches Java project archives from GHTorrent and stores them under `data/raw/`.
2. **Extraction** – `code/data/extract_commits.py` parses commit metadata; `code/data/extract_metrics.py` runs *lizard* on each source file.
3. **Labeling** – `code/data/label_bug_fixes.py` creates `bug_label`.
4. **Validation** – `code/data/validate_bug_labels.py` audits a random sample to ensure ≥ 85 % precision.
5. **Pre‑processing** – `code/data/preprocess.py` imputes, log‑transforms, and drops rows with excessive missingness.
6. **Splitting** – `code/data/split_dataset.py` performs a project‑level stratified split and writes the `split` column.
7. **Modeling** – `code/modeling/*` consumes the processed Parquet file and writes model artefacts and predictions under `data/model/`.

Each pipeline stage writes a **checksum file** (`*.sha256`) alongside its output to enable reproducibility checks.

## 6. Storage & Access

* **Parquet** (`dataset.parquet`) – columnar storage for efficient analytics and ML training.
* **CSV** (`data/model/corrected_pvalues.csv`, `thresholds.csv`) – human‑readable results for reporting.
* **Pickle** (`primary.pkl`, `alternative.pkl`) – serialized scikit‑learn estimators.

The repository’s `requirements.txt` includes `pandas`, `pyarrow`, and `fastparquet` to read/write these formats.

## 7. Future Extensions

* Adding **language‑agnostic** metrics for non‑Java projects.
* Persisting **code embeddings** (e.g., from CodeBERT) as additional features.
* Storing **issue‑level** metadata (severity, component) to enrich the target variable.

---
*End of Document*