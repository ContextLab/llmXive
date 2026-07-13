# Data Model: llmXive follow-up: extending "Intern-Atlas: A Methodological Evolution Graph as Research Infrastruct"

## Overview

This document defines the data structures used throughout the project, ensuring consistency between the extraction, training, and validation phases. All data is stored in CSV or Parquet format under `data/processed/`.

## Entities

### 1. MethodNode (Raw & Processed)

Represents a single methodological paper in the Intern-Atlas graph.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `paper_id` | string | Unique identifier for the paper (e.g., DOI or internal ID). | Intern-Atlas |
| `title` | string | Full title of the paper. | Intern-Atlas |
| `year` | integer | Publication year (2010-2018). | Intern-Atlas |
| `outgoing_edges` | list[dict] | List of edges: `{"target_id": str, "type": str}`. | Intern-Atlas |
| `incoming_citations` | integer | Total number of incoming citations. | Intern-Atlas |
| `field_of_study` | string | Domain classification (e.g., "Machine Learning", "Biology"). | Intern-Atlas |
| `publication_venue` | string | Journal or conference name. | Intern-Atlas |

### 2. RetractionLabel

External truth label mapped to a MethodNode.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `paper_id` | string | Matching paper ID. | Retraction Watch DB |
| `status` | integer | 1 (Fragile), 2 (Retraction-Only), 0 (Robust). | Retraction Watch DB |
| `reason` | string | Specific reason for retraction (if applicable). | Retraction Watch DB |
| `source` | string | "Retraction Watch" or "Replication Index". | Retraction Watch DB |

### 3. TopologicalFeatures

Derived record for each MethodNode, ready for modeling.

| Field | Type | Description | Calculation |
| :--- | :--- | :--- | :--- |
| `paper_id` | string | Foreign key to MethodNode. | Inherited |
| `bottleneck_resolution_ratio` | float | Ratio of (`improves` + `replaces`) edges to total outgoing. | FR-002 |
| `branching_entropy` | float | Shannon entropy of downstream edge types. | FR-003 |
| `citation_count` | integer | Total incoming citations. | Inherited |
| `label` | integer | 1 (Fragile), 0 (Robust). (Retraction-Only excluded from primary model). | FR-004 |

### 4. ModelResult

Record storing performance metrics.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "Topological" or "Baseline". |
| `auc_roc` | float | Area Under the ROC Curve. |
| `precision` | float | Precision score. |
| `recall` | float | Recall score. |
| `f1_score` | float | F1 score. |
| `stability_flag` | boolean | True if VIF > 5 or MI > 0.1. |
| `threshold_sweep` | dict | FPR/FNR for cutoffs {0.3, 0.5, 0.7}. |

## Data Flow

1.  **Raw Data**: `data/raw/intern_atlas_graph.json`, `data/raw/retraction_watch.csv`.
2.  **Extraction**: `run_extraction.py` -> `data/processed/feature_dataset.csv` (contains `TopologicalFeatures` + `RetractionLabel`).
3.  **Training**: `run_training.py` reads `feature_dataset.csv`, splits into train/val, trains models, outputs `data/processed/model_results.json` and `data/processed/permutation_results.csv`.
4.  **Artifacts**: All files are checksummed and recorded in `state/...yaml`.