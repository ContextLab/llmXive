# Data Model: FastContext-Lite

## Overview
This document defines the data schemas for the FastContext-Lite pipeline, ensuring strict adherence to Constitution Principle III (Data Hygiene) and Principle IV (Single Source of Truth). All data flows are unidirectional: Raw -> Processed -> Results.

## Raw Data (Input)
**Source**: SWE-bench (`princeton-nlp/SWE-bench`)
**Format**: JSON/Parquet (streamed)
**Schema**:
- `instance_id`: String (Unique identifier)
- `repo`: String (Repository path)
- `test_patch`: String (Ground truth test changes)
- `base_commit`: String
- `patches`: List[Dict] (Code changes)
- `problem_statement`: String

*Note: Raw data is stored in `data/raw/` with a checksum hash.*

## Processed Data (Intermediate)

### 1. Regularity Scores
**File**: `data/processed/regularity_scores.csv`
**Purpose**: Stores the computed structural scores for stratification.

| Column | Type | Description |
| :--- | :--- | :--- |
| `instance_id` | String | Unique repo ID |
| `repo` | String | Repository path |
| `dir_score` | Float | Directory naming consistency (0-1) |
| `test_score` | Float | Test file placement score (0-1) (Normalized relative path distance) |
| `import_score` | Float | Import pattern adherence (0-1) (Graph density) |
| `regularity_score` | Float | Weighted composite (0-1) |
| `split` | String | "Regular" or "Irregular" |

### 2. Ground Truth Annotations
**File**: `data/processed/ground_truth_annotations.csv`
**Purpose**: Maps instance IDs to ground-truth relevant files.
**Schema**:
- `instance_id`: String
- `ground_truth_files`: String (JSON-encoded list of file paths)

## Results Data (Output)
**File**: `data/results/metrics.csv`
**Purpose**: Primary source of truth for analysis and paper generation.

| Column | Type | Description |
| :--- | :--- | :--- |
| `instance_id` | String | Unique ID |
| `split` | String | "Regular" or "Irregular" |
| `method` | String | "FastContext-Lite" or "FastContext-Original" |
| `context_precision` | Float | Precision against ground truth (IoU) |
| `total_tokens` | Integer | Token count used |
| `latency_ms` | Float | Wall-clock latency in ms |
| `regularity_score` | Float | The score associated with this instance |
| `hardware_efficiency` | Float | Normalized efficiency metric (Precision/Token) |

## Statistical Analysis Output
**File**: `data/results/statistical_analysis.json`
**Schema**:
```json
{
  "test_type": "paired_t_test",
  "dataset": "Regular",
  "metrics": {
    "precision": { "t_stat": float, "p_value": float, "effect_size": float },
    "latency": { "t_stat": float, "p_value": float, "effect_size": float }
  },
  "boundary_analysis": {
    "threshold_score": float,
    "degradation_percentage": float
  }
}
```

## Data Hygiene Rules
1. **Immutability**: Files in `data/raw` and `data/processed` are never modified in place.
2. **Checksums**: Every file written to `data/` is checksummed (SHA-256) and recorded in `state/...yaml`.
3. **PII**: No personally identifiable information is allowed in `data/`. SWE-bench is open source and PII-free.