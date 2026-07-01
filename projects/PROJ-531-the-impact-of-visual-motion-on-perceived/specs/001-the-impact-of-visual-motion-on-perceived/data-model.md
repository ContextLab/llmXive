# Data Model: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

## Overview

This document defines the data structures used throughout the project, ensuring consistency between raw data acquisition, preprocessing, modeling, and output. All data is stored in `data/` (raw) and `data/processed/` (cleaned).

## Entity Definitions

### 1. MotionFeature

Represents a measurable motion parameter from interaction logs.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `feature_type` | string | Type of motion feature (e.g., "latency", "smoothness", "lead_time") | Enum: ["latency", "smoothness", "lead_time"] |
| `value` | float | Numeric value of the feature | ≥ 0 |
| `unit` | string | Unit of measurement | "ms" or "dimensionless" |
| `source_dataset` | string | Name of the source dataset or "synthetic" | Non-empty string |
| `participant_id` | string | Unique identifier for the participant | UUID format |

### 2. AgencyScore

Represents a participant's subjective agency rating.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `participant_id` | string | Unique identifier for the participant | UUID format |
| `scale_items` | array[int] | Array of Likert responses (1-7) | Length ≥ 3, values 1-7 |
| `aggregated_score` | float | Continuous score (mean or sum) | 0.0 - 100.0 |
| `instrument_name` | string | Name of the questionnaire instrument | Non-empty string |
| `validity_flag` | boolean | Whether instrument meets FR-013 (DOI/citations) | True/False |

### 3. AnalysisResult

Represents output from statistical modeling.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `model_type` | string | Type of model used | Enum: ["regression", "random_forest"] |
| `feature_importance` | map[string, float] | Importance scores for each feature | Values ≥ 0 |
| `statistical_significance` | map[string, float] | P-values for each feature | 0.0 - 1.0 |
| `cross_validation_metrics` | map[string, float] | R², RMSE, etc. | Depends on metric |
| `vif_scores` | map[string, float] | Variance Inflation Factor for each predictor | ≥ 1.0 |

## Data Flow

1.  **Raw Data**: Downloaded/generated into `data/raw/` (CSV/Parquet).
2.  **Preprocessing**: Extract motion features and agency scores; handle missing values; compute VIF.
3.  **Cleaned Data**: Stored in `data/processed/analysis_ready.csv`.
4.  **Model Output**: Stored in `data/processed/model_results.json`.
5.  **Visualization**: Generated plots saved to `data/processed/figures/`.

## Constraints & Validations

-   **Missing Values**: Observations with missing motion or agency variables are removed (US-1).
-   **Collinearity**: If VIF ≥5, the feature is excluded from multivariate models.
-   **Outcome Variance**: If agency score variance is low (e.g., most ratings 4/5), a warning is logged.
-   **Instrument Validity**: Only datasets with `validity_flag=True` are used for primary analysis.
