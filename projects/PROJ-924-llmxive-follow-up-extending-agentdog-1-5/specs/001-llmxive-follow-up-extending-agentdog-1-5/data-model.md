# Data Model: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Overview

This document defines the data structures used throughout the project, ensuring consistency between data ingestion, processing, and output. All data is stored in CSV or JSONL formats for compatibility with `pandas` and `datasets`.

## Entity Definitions

### 1. TaxonomyCentroid
Represents the fixed vector embedding for a specific risk category in the AgentDoG 1.5 taxonomy.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `category_id` | string | Unique identifier for the category (e.g., "P1-Prompt-Injection") | Required, Unique |
| `category_name` | string | Human-readable name of the risk category | Required |
| `definition` | string | Original text definition from the taxonomy | Required |
| `embedding_vector` | list[float] | High-dimensional float vector (normalized) | Length=384, Range=[-1, 1] |
| `source_version` | string | Version of the taxonomy source used | Required |

### 2. AgentLog
Represents an input interaction log to be analyzed.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `log_id` | string | Unique identifier for the log (UUID or hash) | Required, Unique |
| `text` | string | The raw text content of the interaction | Required, MaxLength=10000 |
| `source` | string | Origin of the log (e.g., "synthetic", "production") | Optional |
| `timestamp` | string | ISO 8601 timestamp of the log | Optional |
| `is_empty` | boolean | Flag if text is empty or whitespace | Computed |

### 3. DriftResult
The output of the drift scoring process for a single log.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `log_id` | string | Reference to the AgentLog | Required |
| `drift_score` | float | Minimum cosine distance to any centroid | Range=[0.0, 2.0] |
| `nearest_category_id` | string | ID of the closest taxonomy centroid | Required |
| `nearest_distance` | float | Exact distance to the nearest centroid | Range=[0.0, 2.0] |
| `flagged_for_review` | boolean | True if score > threshold (e.g., 2 SD above mean) | Computed |

### 4. AnnotationLabel
Ground truth label assigned by human annotators.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `log_id` | string | Reference to the AgentLog | Required |
| `label` | string | "novel_attack", "known_attack", "benign" | Required |
| `annotator_id` | string | ID of the human annotator | Required |
| `confidence` | float | Annotator's confidence in the label (0-1) | Range=[0.0, 1.0] |
| `blinded` | boolean | Confirmation that annotator was blinded to Drift Score | Required, True |
| `independent_taxonomy_source` | string | Reference to the taxonomy used (e.g., "OWASP Top 10 for LLM v1.0") | Required |

## Data Flow

1. **Ingestion**: `AgentLog` data is loaded from `data/raw/logs.jsonl`.
2. **Processing**:
   - `TaxonomyCentroid` vectors are loaded/generated.
   - `DriftResult` is computed for each `AgentLog`.
   - Results are saved to `data/processed/drift_scores.csv`.
3. **Stratification**: `DriftResult` is split into high/low bins; `AnnotationLabel` is generated via manual process (simulated in code for testing).
   - **Blinding**: The `drift_score` column is explicitly removed before generating the CSV for annotators.
4. **Analysis**: `DriftResult` and `AnnotationLabel` are joined to compute statistics.

## Storage Constraints

- **RAM**: All embeddings and intermediate DataFrames must fit within 4GB.
- **Disk**: Raw data is immutable; processed data is derived and checksummed.
- **PII**: No personally identifiable information is stored in `data/processed/`.