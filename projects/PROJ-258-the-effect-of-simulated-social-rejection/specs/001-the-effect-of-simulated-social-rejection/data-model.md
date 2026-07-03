# Data Model: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Overview

This document defines the data structures used throughout the analysis pipeline. It ensures that data ingestion, preprocessing, and analysis adhere to the schema constraints required for valid statistical testing.

## Entities

### 1. RawDatasetRecord
Represents a single row from the ingested raw dataset.
*   **participant_id**: `string` (Unique identifier for the participant).
*   **condition**: `string` (e.g., "Rejection", "Control", "Reward").
*   **reaction_time_ms**: `float` (Reaction time in milliseconds).
*   **mood_rating**: `float` (Self-reported mood, e.g., 1-7 scale).
*   **source_file**: `string` (Origin filename).
*   **timestamp_ingested**: `datetime`.
*   **is_single_cohort**: `boolean` (True if the dataset contains both tasks for the same participant).

### 2. PreprocessedRecord
Cleaned and normalized data ready for analysis.
*   **participant_id**: `string`.
*   **rejection_group**: `boolean` (True if condition == "Rejection").
*   **mean_rt**: `float` (Mean RT per participant per condition, normalized).
*   **mean_mood**: `float` (Mean mood per participant per condition).
*   **outlier_flag**: `boolean` (True if RT > Q3 + 1.5*IQR within condition group).
*   **design_type**: `string` ("Within-Subjects", "Between-Subjects", or "Unavailable").
    *   *Note*: This field is the explicit trigger for the adaptive ANOVA logic in `analysis.py`.

### 3. AnalysisResult
Output of the statistical tests.
*   **test_type**: `string` (e.g., "Mixed_ANOVA", "OneWay_ANOVA").
*   **f_statistic**: `float`.
*   **p_raw**: `float`.
*   **p_fdr**: `float` (Benjamini-Hochberg corrected).
*   **effect_size**: `float` (e.g., eta-squared).
*   **power_estimate**: `float` (Estimated power for the effect).
*   **alpha_threshold**: `float`.
*   **significant**: `boolean`.
*   **modulation_claim_valid**: `boolean` (False if design is Between-Subjects).

## Data Flow

1.  **Ingestion**: `RawDatasetRecord` created. Validation checks for required columns and `is_single_cohort` flag.
2.  **Preprocessing**: `RawDatasetRecord` → `PreprocessedRecord`. Outliers flagged/removed. `design_type` is set based on `is_single_cohort`.
3.  **Analysis**: `PreprocessedRecord` → `AnalysisResult`. FDR correction applied. Power analysis performed.
4.  **Reporting**: `AnalysisResult` → Final Report (JSON/Markdown).

## Constraints

*   **Memory**: Total dataset size must not exceed a manageable threshold suitable for the experimental setup. If `len(RawDatasetRecord) > 500000`, sampling is applied.
*   **Integrity**: No in-place modification of raw data. All transformations create new files.
*   **Missing Data**: If `reaction_time_ms` is missing, the record is dropped with a log entry.
*   **Design Validity**: If `design_type` is "Between-Subjects", `modulation_claim_valid` must be set to `False`.

