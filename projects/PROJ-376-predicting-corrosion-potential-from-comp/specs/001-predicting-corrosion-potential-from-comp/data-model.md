# Data Model: Predicting Corrosion Potential from Composition and Environment

## Overview

This document defines the data schemas for the project, ensuring strict adherence to the "Composition-Environment Feature Integrity" principle (Constitution VI). All data transformations produce new files, and raw data is preserved.

## Entity Definitions

### 1. AlloyRecord
Represents the chemical composition of a metallic alloy.
*   **Primary Key**: `alloy_id` (UUID or generated hash).
*   **Attributes**:
    *   `alloy_name`: String (e.g., "SS304").
    *   `cluster_id`: String (e.g., "Cluster_0", "Cluster_1"). *Derived from hierarchical agglomerative clustering of elemental weight fractions using cosine similarity threshold 0.90. If < 3 clusters are found, the pipeline halts.*
    *   `composition`: Object (Key: Element Symbol, Value: Weight Fraction). *Normalized to sum to 1.0.*
    *   `source`: String (e.g., "NIST", "Mock" - *Mock only for fixtures*).

### 2. EnvironmentRecord
Represents the testing conditions.
*   **Primary Key**: `env_id` (UUID).
*   **Attributes**:
    *   `ph`: Float (Numeric pH). *Records with missing pH are excluded.*
    *   `temperature_celsius`: Float.
    *   `electrolyte_type`: String (Categorical: "Saline", "Acidic", "Alkaline", "Other").
    *   `source`: String.

### 3. CorrosionMeasurement
The target observation linking an alloy and environment.
*   **Primary Key**: `measurement_id` (UUID).
*   **Attributes**:
    *   `alloy_id`: FK -> AlloyRecord.
    *   `env_id`: FK -> EnvironmentRecord.
    *   `corrosion_potential_mv`: Float (Target Variable, mV vs SHE).
    *   `timestamp`: DateTime (if available).
    *   `is_outlier`: Boolean (True if pH outside [0, 14]).

### 4. ModelResult
Stores the output of the training phase.
*   **Attributes**:
    *   `model_type`: String ("RandomForest", "GradientBoosting").
    *   `r2_score`: Float.
    *   `rmse_mv`: Float.
    *   `hyperparameters`: Object (JSON).
    *   `feature_importance`: Object (Map: Feature Name -> Importance Score).
    *   `p_values`: Object (Map: Feature Name -> P-value).
    *   `permutation_count`: Integer (2000).

## Data Flow

1.  **Raw Ingestion**:
    *   `data/raw/nist_raw.jsonl`: Unprocessed NIST data.
2.  **Processing**:
    *   `data/processed/merged_dataset.parquet`: Unified dataset with normalized composition and environment.
    *   `data/processed/train_set.parquet`: Training split (derived from clustering).
    *   `data/processed/test_set.parquet`: Test split (derived from clustering, no cluster overlap).
3.  **Results**:
    *   `data/results/model_metrics.json`: R², RMSE, and baseline comparison.
    *   `data/results/feature_importance.json`: Permutation importance and p-values (2000 permutations).

## Constraints & Validation Rules

*   **Composition Normalization**: Sum of all weight fractions in `AlloyRecord.composition` MUST be within `0.99 <= sum <= 1.01`.
*   **pH Range**: `EnvironmentRecord.ph` MUST be numeric. Records with missing pH are **excluded**. Values outside `[0, 14]` are flagged as outliers.
*   **Split Integrity**: The `test_set` MUST contain zero `cluster_id` values present in the `train_set`.
*   **Minimum Cluster Count**: The clustering algorithm MUST yield at least 3 distinct clusters. If < 3, the pipeline halts.
*   **Missing Data**: Records with missing `corrosion_potential_mv` are dropped. Records with missing `pH` are **excluded**.
*   **Permutation Count**: Significance testing MUST use 2000 permutations.