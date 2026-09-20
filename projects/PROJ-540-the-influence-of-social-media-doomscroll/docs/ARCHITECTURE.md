# System Architecture

This document outlines the architectural design of the PROJ-540 research pipeline.

## Design Principles

1. **Modularity**: Each research step (Ingestion, Cleaning, Modeling, etc.) is encapsulated in a dedicated module.
2. **Fail-Loud**: The system raises explicit exceptions on data fetch failures or validation errors rather than falling back to synthetic data.
3. **Reproducibility**: All random processes are seeded and logged.
4. **Traceability**: Every output artifact references the specific code path and configuration used to generate it.

## Component Overview

### 1. Configuration (`code/config.py`)
Central hub for project settings.
- Loads YAML configuration.
- Manages random seeds (validation and application).
- Resolves dataset URLs.
- Ensures directory existence.

### 2. Ingestion (`code/ingest.py`)
Responsible for external data acquisition.
- `download_data()`: Fetches raw data from the configured URL.
- `validate_schema()`: Ensures required columns exist.
- Outputs: `data/raw/parsed_data.csv`.

### 3. Cleaning (`code/clean.py`)
Data preparation and power enforcement.
- `load_cleaned_data()`: Reads raw data.
- `validate_cleaned_data()`: Checks for nulls in critical fields.
- `save_cleaned_data()`: Writes to `data/processed/analysis_data.csv`.
- **Power Check**: Halts execution if $N < 130$ (Raising `PowerLimitationError`).

### 4. Modeling (`code/model.py`)
Statistical analysis engine.
- `calculate_correlation()`: Pearson/Spearman coefficients.
- `fit_regression_model()`: OLS regression using `statsmodels`.
- `check_assumptions()`: Linearity, Homoscedasticity, Normality.
- `check_proxy_anxiety()`: Handles construct validity flags.

### 5. Validity (`code/validity.py`)
- `check_construct_validity()`: Detects mathematical coupling between `baseline_anxiety` and `anxiety_score`.

### 6. Robustness (`code/robustness.py`)
- `run_robustness_check()`: Conditional analysis on high-engagement subsets.

### 7. Visualization (`code/viz.py`)
- Generates diagnostic plots (Residuals, Q-Q) and result scatter plots.
- Outputs: `outputs/diagnostics_residuals.png`, `outputs/plot.png`.

### 8. Reporting (`code/report_generator.py`)
- Aggregates JSON results from all stages.
- Generates `outputs/final_report.md`.

## Data Flow

1. **Config** -> **Ingest** (Download)
2. **Ingest** -> **Clean** (Parse & Validate)
3. **Clean** -> **Model** (Fit & Diagnose)
4. **Model** -> **Robustness** (Conditional Check)
5. **Model** + **Robustness** -> **Viz** (Plots)
6. **All Results** -> **Report Generator** (Final Output)

## Error Handling

Custom exceptions are defined in `code/exceptions.py`:
- `PowerLimitationError`: Triggered when sample size is insufficient.
- `MathematicalCouplingError`: Triggered when variables are not distinct.
- `DataValidationError`: Triggered on schema mismatches.
- `ConfigurationError`: Triggered on missing config values.
