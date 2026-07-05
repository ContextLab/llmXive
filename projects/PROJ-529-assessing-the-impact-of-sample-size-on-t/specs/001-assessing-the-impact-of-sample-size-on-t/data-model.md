# Data Model: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## 1. Entity Relationship Overview

The data model consists of three primary layers:
1.  **Raw Input**: Component studies from meta-analyses (or synthetic generation parameters).
2.  **Subsamples**: Bootstrap samples generated at specific `k`, including the random seed used.
3.  **Metrics**: Aggregated stability and coverage statistics, including the estimator type used.

## 2. Schema Definitions

### 2.1 Raw Meta-Analysis Component
Represents a single study within a meta-analysis.
*   **ID**: `meta_id` (string), `study_id` (string)
*   **Fields**: `effect_size` (float), `se_effect` (float), `weight` (float, derived), `true_effect` (float, optional, simulation only)

### 2.2 Subsample Record
Represents one bootstrap iteration at a specific study count.
*   **ID**: `subsample_id` (UUID), `meta_id` (string)
*   **Fields**: 
    *   `k` (int): Number of studies in the subsample.
    *   `iteration` (int): Bootstrap iteration index.
    *   `seed` (int): **The random seed used for this specific iteration** (Critical for reproducibility per Constitution Principle VI).
    *   `pooled_effect` (float): Weighted mean of the subsample.
    *   `se_pooled` (float): Standard error of the pooled effect.
    *   `ci_lower` (float): Lower bound of 95% CI.
    *   `ci_upper` (float): Upper bound of 95% CI.
    *   `model_type` (string): "FE", "RE_DL", or "RE_REML" (Explicitly tracks the estimator used to detect boundary artifacts).

### 2.3 Aggregated Metrics
One row per `meta_id` + `k` + `model_type`.
*   **ID**: `meta_id`, `k`, `model_type`
*   **Fields**: 
    *   `stability_sd` (float): Standard deviation of pooled effects across bootstrap iterations.
    *   `agreement_rate` (float): Proportion of subsamples where CI contains the full-sample estimate (Reference Agreement Rate).
    *   `coverage_rate` (float): Proportion of subsamples where CI contains the true effect (Simulation Mode only).
    *   `n_subsamples` (int): Number of bootstrap iterations used.
    *   `full_sample_estimate` (float): The reference value used for agreement calculation.

## 3. Data Flow

1.  **Ingestion**: `raw_meta.csv` (from Cochrane/Campbell) or `synthetic_params.yaml` → `data/raw/`.
2.  **Subsampling**: `subsample.py` reads input, generates `subsample_data.parquet` (including `seed` and `model_type`).
3.  **Modeling**: `models.py` reads `subsample_data.parquet`, writes `metrics_raw.parquet`.
4.  **Aggregation**: `metrics.py` aggregates to `metrics_summary.csv`.
5.  **Analysis**: `analysis.py` reads `metrics_summary.csv`, outputs `thresholds.json` and plots.

## 4. Constraints & Validation Rules

*   **Effect Size**: Must be finite (no NaN/Inf).
*   **SE**: Must be > 0 (epsilon applied if 0).
*   **k**: Must be ≥ 3 and ≤ N (total studies in MA).
*   **Seed**: Must be an integer > 0.
*   **Model Type**: Must be one of `["FE", "RE_DL", "RE_REML"]`.
*   **Agreement Rate**: Must be in [0, 1].