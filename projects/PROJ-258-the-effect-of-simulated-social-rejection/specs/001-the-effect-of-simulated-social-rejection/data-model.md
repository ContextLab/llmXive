# Data Model: 001-social-rejection-reward

## Overview

This document defines the data structures used throughout the pipeline: raw ingestion, preprocessing, and analysis output. All data is stored in local files (`data/raw/`, `data/processed/`) and validated against schemas defined in `contracts/`.

## Entities

### 1. Raw Dataset Record
Represents the raw data loaded from the source (Parquet/CSV).
*   **Source**: OpenNeuro (HuggingFace) ds000208.
*   **Format**: Parquet.
*   **Key Fields**:
    *   `participant_id`: Unique identifier (string).
    *   `task`: Task name (e.g., "cyberball").
    *   `condition`: Experimental condition (e.g., "rejection", "control").
    *   `reaction_time`: Response time in ms (float).
    *   `mood_rating`: Self-reported mood score (float).
    *   `timestamp`: Event timestamp (optional).

### 2. Preprocessed Record
Cleaned and normalized data ready for analysis.
*   **Transformation**: Outlier removal (IQR per condition), normalization.
*   **Key Fields**:
    *   `participant_id`: (Inherited).
    *   `condition`: (Inherited).
    *   `rt_normalized`: Normalized reaction time.
    *   `is_outlier`: Boolean flag.
    *   `mood_avg`: Mean mood rating per condition.

### 3. Analysis Result
Output of the statistical model.
*   **Format**: JSON/CSV.
*   **Key Fields**:
    *   `test_type`: "One_Way_ANOVA".
    *   `design_type`: "Within-Subjects".
    *   `f_value`: F-statistic.
    *   `p_raw`: Raw p-value.
    *   `p_fdr`: FDR-corrected p-value.
    *   `effect_size`: Eta-squared or Cohen's d.
    *   `alpha_sensitivity`: Dict of {0.01: bool, 0.05: bool, 0.1: bool}.

## Data Flow

1.  **Ingestion**: Raw Parquet -> `data/raw/` (Checksummed).
2.  **Validation**: Check for required columns (`participant_id`, `condition`, `reaction_time`, `mood_rating`).
3.  **Preprocessing**: Raw -> `data/processed/analysis_ready.csv` (Cleaned, outliers flagged).
4.  **Analysis**: `analysis_ready.csv` -> `results/analysis_output.json`.
5.  **Reporting**: `analysis_output.json` -> `paper/report.md`.

## Constraints

*   **Memory**: All intermediate files must fit in GB RAM.
*   **PII**: No personally identifiable information allowed. `participant_id` must be anonymized.
*   **Immutability**: Raw data in `data/raw/` is never modified.
