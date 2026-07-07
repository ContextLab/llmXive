# Data Model: Evaluating the Robustness of Statistical Methods to Common Data Errors

## Overview

This document defines the data structures used throughout the simulation pipeline. It ensures consistency between data ingestion, error injection, statistical testing, and result aggregation.

## Entities

### 1. Dataset
A collection of observations with known ground-truth parameters.
-   **Source**: Verified URL or synthetic generator.
-   **Type**: Numerical, Categorical, or Mixed.
-   **Attributes**: `dataset_id`, `source_url`, `original_checksum`, `variable_list`.

### 2. ErrorConfiguration
Parameters defining the error injection process.
-   **Attributes**: `error_type` (replacement, misclassification, mcar), `rate` (0.01, 0.05, 0.10, 0.20), `seed`.

### 3. InferenceMetric
A result record containing the outcome of a statistical test.
-   **Attributes**: `test_type`, `error_rate`, `p_value`, `ci_lower`, `ci_upper`, `effect_size`, `type_i_error_flag` (boolean), `ci_coverage_flag` (boolean), `seed`.

### 4. DegradationCurve
Aggregated results for visualization.
-   **Attributes**: `test_type`, `error_type`, `error_rates` (list), `type_i_error_rates` (list), `ci_coverage_rates` (list), `effect_size_bias` (list).

## Data Flow

1.  **Raw Data**: Downloaded from verified URLs and stored in `data/raw/`.
2.  **Processed Data**: Error-injected versions stored in `data/processed/` with filenames encoding the error configuration (e.g., `dataset_id_error_type_rate_seed.csv`).
3.  **Results**: Test outcomes stored in `results/metrics/` as JSON/CSV.
4.  **Plots**: Visualizations stored in `results/plots/` as PNG.

## Schema Definitions

### Input Dataset Schema (CSV/Parquet)
-   `variable_name`: String (column name)
-   `variable_type`: String (numerical, categorical)
-   `values`: List of values (numeric or string)

### Output Metrics Schema (JSON)
-   `dataset_id`: String
-   `test_type`: String (t-test, anova, chi-squared, linear_regression)
-   `error_type`: String (replacement, misclassification, mcar)
-   `error_rate`: Float
-   `p_value`: Float
-   `ci_lower`: Float
-   `ci_upper`: Float
-   `effect_size`: Float
-   `type_i_error`: Boolean
-   `ci_coverage`: Boolean
-   `seed`: Integer

## Constraints

-   **No In-Place Modification**: Raw data is never modified. All transformations produce new files.
-   **Checksums**: Every file in `data/raw` and `data/processed` must have a corresponding checksum record.
-   **Reproducibility**: All random seeds must be recorded in the metadata of each processed dataset and result.
