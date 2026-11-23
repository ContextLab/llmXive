# Data Processing Pipeline

## Overview

This document describes the data processing workflow, from raw input to final analysis-ready datasets. The pipeline is designed to handle both real public datasets and synthetic data generation for validation.

## Input Data Requirements

The system accepts input data in CSV or JSON format. The following columns are **required**:

- `pre_test_score`: Numeric value representing the pre-intervention assessment score.
- `post_test_score`: Numeric value representing the post-intervention assessment score.
- `instruction_type`: Categorical string indicating the type of instruction (e.g., "embodied", "static").

**Optional**:
- `covariates`: A JSON string or nested dictionary containing additional variables for collinearity checks.

## Processing Steps

### 1. Data Loading and Validation

The `load_public_dataset` function in `code/src/data_loader.py` performs the following:
- Reads the input file (CSV or JSON).
- Validates the presence of required columns.
- Checks for data types and missing values.

**Automatic Fallback (FR-008)**:
If the `instruction_type` column is missing, the system **automatically invokes** the `SyntheticDataGenerator` to create a labeled dataset. This ensures the pipeline can proceed without manual intervention, maintaining determinism.

### 2. Gain Score Calculation

For each valid row, the learning gain is computed:
$$ \text{Gain} = \text{post\_test\_score} - \text{pre\_test\_score} $$

- Rows with missing `pre_test_score` or `post_test_score` are **excluded**.
- Excluded rows are logged to `data/derivation_logs/skipped_records.log` with a reason code.

### 3. Synthetic Data Generation (Validation Mode)

When running in `--mode=synthetic`, the `SyntheticDataGenerator` class in `code/src/synthetic_gen.py` generates a dataset with:
- Configurable sample size.
- Defined mean differences between groups (ground truth).
- Configurable standard deviations.

**Mapping Log (Constitution Principle VI)**:
For synthetic data, a `mapping_log.json` is generated in `data/synthetic/`. This file documents the causal chain:
`Physics_Action` -> `Virtual_Object_State` -> `Abstract_Principle_Inference`.
This log is **only** generated for Synthetic Mode and is not required for Secondary Analysis Mode.

### 4. Data Aggregation

Processed data is grouped by `instruction_type` to prepare for statistical testing. Summary statistics (mean, std, N) are calculated for each group.

## Output Artifacts

- **Processed Dataset**: `data/processed/cleaned_dataset.csv` (optional intermediate file).
- **Analysis Results**: `data/processed/results.json` (final output).
- **Skipped Records Log**: `data/derivation_logs/skipped_records.log`.
- **Mapping Log**: `data/synthetic/mapping_log.json` (Synthetic Mode only).

## Error Handling

- **Missing Columns**: If required columns are missing and the fallback is not applicable (e.g., in secondary analysis without synthetic option), the system raises a clear error.
- **Invalid Data Types**: Non-numeric scores trigger a validation error.
- **Empty Groups**: If an `instruction_type` has fewer than 2 samples, a warning is issued, and the t-test for that group is skipped.

## Reproducibility

All random operations (e.g., synthetic generation, shuffling) use a deterministic seed managed by `code/src/utils.py`. The seed is set via the `--seed` CLI argument, ensuring that results can be exactly reproduced.