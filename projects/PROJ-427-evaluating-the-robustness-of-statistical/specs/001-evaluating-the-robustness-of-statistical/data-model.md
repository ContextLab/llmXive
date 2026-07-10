# Data Model: Evaluating the Robustness of Statistical Methods to Common Data Errors

## Overview

This document defines the data structures used for input configuration, intermediate error-injected datasets, and output metrics. All data is persisted in `data/` and `results/` directories.

## Entities

### 1. Dataset Metadata
Represents the source and characteristics of a raw dataset.
- `id`: Unique identifier (e.g., `uci_har`).
- `source_url`: Verified URL.
- `type`: `numerical`, `categorical`, or `mixed`.
- `checksum`: SHA-256 hash of the raw file.
- `sample_size`: Number of rows.

### 2. ErrorConfiguration
Defines a specific error injection scenario.
- `dataset_id`: Reference to Dataset Metadata.
- `error_type`: `replacement`, `misclassification`, `mcar`.
- `rate`: Float (0.01, 0.05, 0.10, 0.20).
- `seed`: Integer for reproducibility.
- `generated_path`: Path to the processed CSV/Parquet.

### 3. InferenceResult
A single record of a statistical test execution.
- `run_id`: Unique identifier for the simulation run.
- `dataset_id`: Reference.
- `error_config_id`: Reference.
- `test_type`: `t_test`, `anova`, `chi_squared`, `regression`.
- `metric_type`: `type_i_error`, `ci_coverage`, `effect_size_bias`.
- `value`: Float (the calculated metric).
- `true_parameter`: Float (the ground truth used for comparison).
- `p_value`: Float.
- `ci_lower`: Float.
- `ci_upper`: Float.
- `rejection`: Boolean (1 if $p < 0.05$).

### 4. AggregatedMetrics
Summary statistics for a specific condition (Test + Error Type + Rate).
- `test_type`: String.
- `error_type`: String.
- `rate`: Float.
- `mean_type_i_error`: Float.
- `mean_ci_coverage`: Float.
- `mean_bias`: Float.
- `n_iterations`: Integer.

## File Formats

- **Raw Data**: CSV or Parquet (as per source).
- **Processed Data**: CSV (to ensure compatibility with `scipy`/`statsmodels` and easy inspection).
- **Results**: JSON (for easy aggregation and plotting).

## Constraints

- **No PII**: All datasets are verified public; no personal data is committed.
- **Immutability**: Raw files are never overwritten.
- **Schema Validation**: All output JSONs must conform to the contracts defined in `contracts/`.
