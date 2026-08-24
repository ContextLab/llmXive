# Data Model: Predicting Material Degradation Under Cyclic Loading

## Overview

This document defines the data structures used in the pipeline. Given the **absence of verified material fatigue datasets**, the data model is defined based on the **specification requirements** (FR-001) but will be instantiated with **empty or null data** in the actual run, triggering a "Coverage Gap" alert.

The primary artifact is the **Gap Report**, which documents the absence of data.

## Entity Definitions

### 1. MaterialSample
Represents a single experimental entry.
*Note: Since no verified dataset contains these fields, this entity will not be instantiated in the current run.*

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `source_id` | string | Unique identifier from the original dataset. | Raw Data |
| `composition` | map<string, float> | Elemental percentages (e.g., `{"Fe": 98.5, "C": 1.5}`). | Raw Data |
| `loading_params` | object | Loading conditions. | Raw Data |
| `stress_amplitude` | float | Cyclic stress amplitude (MPa). | Raw Data |
| `frequency` | float | Loading frequency (Hz). | Raw Data |
| `r_ratio` | float | Stress ratio (min/max stress). | Raw Data |
| `degradation_metric` | float | Target variable (RUL or stiffness loss). | Raw Data |
| `censored` | boolean | True if the experiment survived without failure. | Raw Data |

### 2. UnifiedDataset
The intermediate processed dataset used for modeling.
*In the current run, this entity will be empty or contain only metadata about the gap.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique row ID. |
| `features` | array<float> | Flattened composition and loading parameters. |
| `target` | float | Degradation metric. |
| `imputation_flags` | array<dict> | Log of which values were imputed and how. |
| `status` | string | "success", "coverage_gap", or "error". |

### 3. ModelResult
Output of the training phase.
*In the current run, this entity will not be instantiated.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "ElasticNet", "RandomForest", or "GradientBoosting". |
| `mean_r2` | float | Mean R² score from 5-fold CV. |
| `std_r2` | float | Standard deviation of R². |
| `feature_importance` | array<float> | Importance scores (if applicable). |
| `p_values` | array<float> | Statistical significance values (if applicable). |

### 4. PredictionInterval
Uncertainty estimate for a prediction.
*In the current run, this entity will not be instantiated.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `point_estimate` | float | Predicted degradation value. |
| `lower_bound` | float | 10th percentile of prediction distribution. |
| `upper_bound` | float | 90th percentile of prediction distribution. |
| `confidence_level` | string | "90%". |

### 5. GapReport
The primary output of the feasibility study.

| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | string | ISO 8601 timestamp. |
| `status` | string | "coverage_gap". |
| `missing_columns` | array<string> | List of required columns not found (e.g., `stress_amplitude`). |
| `sources_checked` | array<string> | List of verified URLs checked. |
| `recommendation` | string | "Acquire new verified dataset" or "Abandon hypothesis". |

## Data Flow

1.  **Ingestion**: Load raw files from verified URLs (NIST/UCI).
2.  **Validation**: Check for presence of `stress_amplitude`, `composition`, etc.
    *   **If missing**: Log error, set `status = "COVERAGE_GAP"`, generate `GapReport`, stop pipeline.
3.  **Preprocessing**: (Skipped if Coverage Gap).
4.  **Modeling**: (Skipped if Coverage Gap).
5.  **Inference**: (Skipped if Coverage Gap).

## Constraints

- **Memory**: All data must fit in 7 GB RAM. If not, subsample.
- **Disk**: All intermediate files must fit in 14 GB.
- **Integrity**: Raw data files are never modified. All transformations create new files with checksums.
- **Termination**: If `status = "COVERAGE_GAP"`, the pipeline exits with code 2.