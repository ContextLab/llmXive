# Data Model: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Overview

This document defines the data structures used to ingest, process, and store data for the pain sensitivity prediction study. The model ensures traceability from raw EEG to final model results, adhering to the "Single Source of Truth" principle.

## Entities

### 1. Participant
Represents an individual in the study.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique participant identifier (e.g., `sub-001`). | Primary Key, Non-null. |
| `heat_pain_threshold` | float | Heat-pain threshold in °C. | Non-null, > 0. |
| `age` | integer | Age in years. | Optional. |
| `gender` | string | Gender identity. | Optional, categorical. |
| `valid_eeg_minutes` | float | Duration of valid EEG after ICA. | Must be ≥ 4.0 for inclusion. |
| `exclusion_reason` | string | Reason for exclusion if any. | Null if included. |

### 2. DataChunk
Represents a memory-efficient batch of raw EEG data used to satisfy the GB RAM constraint (as per updated FR-001 and spec Key Entities).

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `chunk_id` | integer | Unique chunk identifier. | Primary Key. |
| `participant_id` | string | FK to Participant. | Non-null. |
| `data_path` | string | Path to the memory-mapped file or temporary buffer. | Non-null. |
| `start_time` | float | Start time of the chunk in seconds. | Non-null. |
| `end_time` | float | End time of the chunk in seconds. | Non-null. |
| `status` | string | Status of the chunk (e.g., "loaded", "processed", "excluded"). | Enum. |

### 3. MicrostateFeature
Represents a derived metric from the EEG preprocessing pipeline.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | FK to Participant. | Non-null. |
| `feature_name` | string | Name of the feature (e.g., `MS_A_Duration`, `Spectral_Beta_Power`). | Non-null, Enum of features. |
| `value` | float | Normalized or raw value of the feature. | Non-null, No NaN. |
| `standard_error` | float | Standard error of the estimate (if applicable). | Optional. |

### 4. ModelResult
Represents the output of the regression analysis.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `run_id` | string | Unique identifier for the model run. | Primary Key. |
| `pearson_r` | float | Correlation between predicted and observed thresholds. | Non-null. |
| `p_value` | float | Empirical p-value from global permutation test. | Non-null, [0, 1]. |
| `mae` | float | Mean Absolute Error. | Non-null. |
| `ci_lower` | float | Lower bound of 95% CI. | Non-null. |
| `ci_upper` | float | Upper bound of 95% CI. | Non-null. |
| `n_permutations` | integer | Number of permutations performed. | ≥ 1000 (or 500 if limited). |
| `n_bootstrap` | integer | Number of bootstrap resamples. | ≥ 200. |

### 5. DiagnosticReport
Stores statistical validation metrics.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `feature_name` | string | Name of the predictor. | FK to MicrostateFeature. |
| `coefficient` | float | Elastic Net coefficient. | Non-null. |
| `importance_score` | float | Permutation importance score. | Non-null. |
| `p_value_raw` | float | Raw p-value (from Permutation Importance). | Non-null. |
| `p_value_fdr` | float | FDR-adjusted p-value. | Non-null. |
| `vif` | float | Variance Inflation Factor. | Non-null. |
| `is_significant` | boolean | True if `p_value_fdr < 0.05`. | Derived. |
| `is_collinear` | boolean | True if `vif > 10`. | Derived. |

## Data Flow

1.  **Raw Input**: `data/raw/*.parquet` or `data/raw/*.csv` (Verified dataset).
2.  **Chunking**: Raw data is split into `DataChunk` entities and loaded into memory-mapped arrays.
3.  **Preprocessed**: `data/processed/feature_matrix.csv` (30 columns, N rows).
4.  **Model Output**: `artifacts/model_results.json` (ModelResult).
5.  **Diagnostics**: `artifacts/diagnostics.csv` (DiagnosticReport).

## Validation Rules

-   **Completeness**: No NaN values in the final feature matrix.
-   **Consistency**: All `participant_id`s in `MicrostateFeature` must exist in `Participant`.
-   **Thresholds**: Participants with `valid_eeg_minutes < 4.0` are excluded before feature extraction.
-   **Integrity**: `heat_pain_threshold` must be within physiological bounds (e.g., 35°C - 55°C).
-   **Chunking**: Raw data must be processed in `DataChunk` batches to ensure total RAM usage remains within acceptable system limits.
-   **Dataset Existence**: If no verified source for `heat_pain_threshold` exists, the pipeline halts before ingestion.