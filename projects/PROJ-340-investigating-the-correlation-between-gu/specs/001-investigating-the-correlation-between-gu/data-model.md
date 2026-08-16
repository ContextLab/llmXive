# Data Model: Gut Microbiome-Sleep Architecture

## Overview

This document defines the data structures, schemas, and transformations used in the analysis pipeline. It ensures strict adherence to the "Single Source of Truth" (Constitution IV) and "Data Hygiene" (Constitution III) principles.

## Entity Definitions

### 1. MicrobialTaxon
Represents a specific bacterial species or genus.
- `taxon_name` (string): Unique identifier (e.g., "Bacteroides_fragilis").
- `abundance_count` (integer): Raw read count.
- `relative_abundance` (float): Proportion of total reads (0.0 to 1.0).
- `taxonomy_level` (string): "Genus", "Species", etc.
- `clr_value` (float): Centered Log-Ratio transformed value (calculated during preprocessing).

### 2. SleepMetric
Represents a sleep architecture variable.
- `metric_name` (string): e.g., "REM_duration", "SWS_percentage", "Total_Sleep_Time".
- `value` (float): Measured value.
- `unit` (string): "minutes", "percentage", "hours".

### 3. CorrelationResult
Output of the statistical analysis.
- `taxon` (string): Name of the microbial taxon.
- `sleep_metric` (string): Name of the sleep metric.
- `correlation_coefficient` (float): r (for Pearson/Spearman) or beta (for ZINB).
- `p_value_raw` (float): Unadjusted p-value.
- `p_value_adjusted` (float): BH-adjusted p-value.
- `is_significant` (boolean): True if `p_value_adjusted < 0.05`.
- `method_used` (string): "ZINB", "Spearman", "Pearson".
- `direction` (string): "positive" or "negative".
- `effect_size_category` (string): "negligible", "weak", "moderate", "strong".

## Data Flow & Transformations

1.  **Raw Input**: `data/raw/synthetic_data.csv` (or `real_data.csv`).
    - Format: CSV.
    - Columns: `subject_id`, `taxon_1`, `taxon_2`, ..., `REM_duration`, `SWS_duration`, ...
2.  **Validation**: `code/ingest.py` checks for required columns.
    - Output: `data/metadata/required_variables.yaml` (if pass) or `data/results/validation_failure_report.json` (if fail).
3.  **Cleaning**: `code/ingest.py` handles outliers (1.5x IQR) and missing values.
    - Output: `data/processed/cleaned_data.csv`.
4.  **Transformation**: `code/analysis.py` applies **CLR transformation** to predictors.
    - Output: `data/processed/cleaned_data.csv` (updated with CLR columns) or `data/processed/clr_transformed_data.csv`.
5.  **Analysis**: `code/analysis.py` computes correlations.
    - Output: `data/results/correlation_results.csv`.
6.  **Reporting**: `code/reporting.py` aggregates results into JSON.
    - Output: `data/results/correlation_matrix.json` (Single Source of Truth).
7.  **Diagnostics**: `code/diagnostics.py` computes VIF and collinearity.
    - Output: `data/metadata/static_collinearity_map.json`, `data/results/vif_report.json`.
8.  **Sensitivity**: `code/reporting.py` aggregates sensitivity analysis.
    - Output: `data/results/sensitivity_analysis.json`.

## Data Constraints

- **Zero-Inflation**: Handled by ZINB model selection logic.
- **Collinearity**: Perfect multicollinearity detected via rank check; VIF > 5 flagged.
- **Outliers**: Excluded from analysis if > 1.5x IQR from Q1/Q3.
- **Missing Data**: If required variables are missing, pipeline halts with error.
- **Compositional**: CLR transformation is mandatory before correlation/VIF.

## Schema Validation

All CSV inputs must conform to the schema defined in `contracts/dataset_schema.yaml`. The `ingest.py` script validates this before processing.
The primary output `data/results/correlation_matrix.json` must conform to `contracts/output.schema.yaml`.