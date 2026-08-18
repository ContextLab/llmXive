# Data Model: Active Learners as Efficient PRP Rerankers

## Overview
This document defines the schema and flow of data artifacts for the redundancy analysis pipeline. All data is derived from real BEIR datasets or explicitly labeled synthetic injections.

## Input Data

### BEIR Dataset (Raw)
-   **Source**: HuggingFace (via `beir` library).
-   **Format**: JSON/Parquet (converted to internal JSON).
-   **Fields**:
    -   `query_id`: string
    -   `query`: string
    -   `doc_id`: string
    -   `document`: string
    -   `relevance`: integer (0 or 1)

## Intermediate Artifacts

### 1. Injected Datasets (`data/processed/injected_datasets.json`)
-   **Description**: Original BEIR documents plus synthetic duplicates generated via Exact Copy Perturbation.
-   **Source**: `code/injection.py` (FR-001).
-   **Fields**:
    -   `doc_id`: string (unique ID, original or synthetic).
    -   `original_doc_id`: string (link to source, null for originals).
    -   `document`: string (text).
    -   `is_synthetic`: boolean.
    -   `cluster_id`: string (assigned by MinHash-LSH).

### 2. Clusters (`data/processed/clusters.json`)
-   **Description**: Mapping of documents to MinHash-LSH clusters.
-   **Source**: `cluster_engine.py` (FR-005).
-   **Fields**:
    -   `cluster_id`: string.
    -   `members`: list of `doc_id`.
    -   `representative`: string (first member).
    -   `similarity_score`: float (min pairwise similarity in cluster).

### 3. Comparison Log (`data/processed/comparison_log.jsonl`)
-   **Description**: Log of every pairwise comparison made by the active learner.
-   **Source**: `redundancy_detector.py` (FR-004).
-   **Fields** (per line):
    -   `pair_id`: string.
    -   `doc_a_id`: string.
    -   `doc_b_id`: string.
    -   `similarity`: float (Cosine similarity).
    -   `is_wasted`: boolean (true if `similarity > 0.95`).
    -   `outcome`: string (e.g., "ranked", "skipped").

### 4. Unique Subset (`data/processed/unique_subset.json`)
-   **Description**: The set of unique documents (no synthetic duplicates) used for baseline.
-   **Source**: `data_loader.py`.
-   **Fields**: Same as `injected_datasets.json` but `is_synthetic=false` and `cluster_id=null`.

## Output Artifacts

### 1. Flagged Pairs Count (`data/results/flagged_pairs_count.json`)
-   **Description**: Count of wasted calls per seed.
-   **Fields**:
    -   `seed`: integer.
    -   `total_calls`: integer.
    -   `wasted_calls`: integer.
    -   `wasted_ratio`: float.

### 2. NDCG Results (`data/results/us1_baseline_ndcg.json`, `data/results/us1_redundant_ndcg.json`)
-   **Description**: NDCG@10 scores.
-   **Fields**:
    -   `seed`: integer.
    -   `ndcg_at_10`: float.

### 3. Statistical Test Results (`data/results/wilcoxon_wasted_calls.json`)
-   **Description**: Wilcoxon signed-rank test results on **Wasted Call Ratio**.
-   **Fields**:
    -   `statistic`: float.
    -   `p_value`: float.
    -   `bonferroni_adjusted_p`: float.
    -   `significant`: boolean.

### 4. Statistical Report (`data/results/statistical_report.md`)
-   **Description**: Human-readable summary of findings.
-   **Content**: Markdown report with tables, charts (if generated), and interpretation.

## Data Integrity & Traceability
-   **Checksums**: Every intermediate file (`injected_datasets.json`, `clusters.json`) is checksummed (SHA-256) in `state/` before downstream use (FR-008).
-   **Traceability**: `comparison_log.jsonl` contains `pair_id` which links back to `doc_id` in `injected_datasets.json`.
-   **No Fabrication**: All `similarity` scores are computed on-the-fly using `sentence-transformers`. No pre-computed or hardcoded values are used.