# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Overview

This document defines the data structures, schemas, and transformation logic for the project. It ensures that the `ingestion`, `analysis`, and `reporting` modules operate on consistent, validated data.

## Core Entities

### 1. MicrobialTaxon
Represents a specific bacterial species or genus.
- **Attributes**:
  - `taxon_name` (str): The name of the taxon (e.g., "Faecalibacterium prausnitzii").
  - `abundance_count` (int): Raw count from sequencing.
  - `relative_abundance` (float): Normalized abundance (0.0 - 1.0).
  - `zero_inflation_ratio` (float): Proportion of samples with zero count.
  - `distribution_test` (dict): Results of Shapiro-Wilk test (statistic, p_value).
  - `pre_screen_status` (bool): True if the taxon passed the abundance/variance pre-screening step.

### 2. SleepMetric
Represents a sleep architecture variable.
- **Attributes**:
  - `metric_name` (str): Name of the metric (e.g., "REM_duration", "SWS_percentage").
  - `value` (float): Measured value for the subject.
  - `unit` (str): Unit of measurement (e.g., "minutes", "percent").
  - `outlier_status` (bool): True if the value is an outlier (>1.5x IQR).

### 3. CorrelationResult
The output of a statistical test between a taxon and a sleep metric.
- **Attributes**:
  - `taxon` (str): Name of the microbial taxon.
  - `sleep_metric` (str): Name of the sleep metric.
  - `correlation_coefficient` (float | null): The estimated correlation (r for Pearson/Spearman/SparCC). `null` for ZINB.
  - `effect_size_beta` (float | null): The estimated log-rate ratio (beta) for ZINB. `null` for correlation methods.
  - `p_value_raw` (float): Raw p-value.
  - `p_value_adjusted` (float): Benjamini-Hochberg adjusted p-value.
  - `is_significant` (bool): True if adjusted p < 0.05.
  - `method_used` (str): "ZINB", "SparCC", "SpiecEasi", "Spearman", or "Pearson".
  - `direction` (str): "positive" or "negative" based on the sign of the coefficient or beta.
  - `effect_size_category` (str): "negligible", "weak", "moderate", or "strong" based on absolute value thresholds.

### 4. DiagnosticReport
Aggregated diagnostics for the dataset.
- **Attributes**:
  - `collinearity_flags` (list): List of taxa pairs flagged for perfect multicollinearity.
  - `vif_results` (dict): Map of taxon -> VIF score (calculated on Top-N subset).
  - `power_analysis` (dict): { "required_n": int, "observed_n": int, "is_underpowered": bool, "metric_used": str }.
  - `sensitivity_analysis` (dict): { "p_0.01": int, "p_0.05": int, "p_0.10": int }.
  - `pre_screen_summary` (dict): { "total_taxa": int, "passed_taxa": int }.

## Data Flow

1.  **Raw Input**: CSV/TSV file with columns: `subject_id`, `taxon_A`, `taxon_B`, ..., `REM_duration`, `SWS_duration`.
2.  **Validation**: Check for required columns. If missing, halt with error.
3.  **Pre-screening**: Filter taxa by abundance/variance to reduce multiple testing burden.
4.  **Transformation**:
    - Calculate relative abundance.
    - Detect outliers and flag/exclude.
    - Run distribution tests (Shapiro-Wilk, zero-inflation) on `abundance_count` and `value` attributes.
5.  **Analysis**: Run selected correlation models (SparCC, ZINB).
6.  **Correction**: Apply Benjamini-Hochberg correction.
7.  **Output**: JSON/CSV files containing `CorrelationResult` and `DiagnosticReport`.

## Constraints

- **No PII**: `subject_id` must be anonymized (e.g., hash or random UUID).
- **Data Integrity**: Raw data files are never modified; all transformations create new files in `data/processed/`.
- **Type Safety**: All numeric fields must be float/int; missing values must be explicitly handled (imputed or excluded).
