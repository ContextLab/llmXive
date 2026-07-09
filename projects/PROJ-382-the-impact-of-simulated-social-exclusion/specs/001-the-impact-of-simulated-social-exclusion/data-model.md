# Data Model: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

## Entities & Relationships

### 1. Dataset
Represents a single study source.
*   **ID**: `dataset_id` (string, unique hash of source URL + filename)
*   **source_url**: (string) The verified URL used.
*   **raw_file**: (string) Path to raw file in `data/raw/`.
*   **processed_file**: (string) Path to cleaned file in `data/processed/`.
*   **is_valid**: (boolean) True if schema validation passed.
*   **randomized**: (boolean) Flag indicating random assignment.
*   **sample_size**: (integer) Total participants.
*   **exclusion_n**: (integer) Participants in exclusion condition.
*   **rejection_reason**: (string) If invalid, why (e.g., "Missing 'condition' column").

### 2. Participant
Represents a single row in the consolidated dataset.
*   **dataset_id**: (string) FK to Dataset.
*   **condition**: (integer) 0 = Included, 1 = Excluded.
*   **prosocial_amount**: (float) Donation amount.
    *   *Note*: Structural zeros (0) are preserved.
    *   *Missing*: NaN (handled via imputation logic).
*   **outcome_type**: (string) "continuous" or "binary".
*   **is_outlier**: (boolean) Flagged if > 3 SD from mean (for robustness check).

### 3. AnalysisResult
Represents the output of a specific model run.
*   **result_id**: (string) Unique ID.
*   **pool_type**: (string) "Causal" or "Associational".
*   **model_type**: (string) "ZIG", "Hurdle", or "Logistic".
*   **zero_inflation_coefficient**: (float) $\beta$ for the log-odds of zero-inflation (probability of donating).
*   **gamma_coefficient**: (float) $\beta$ for the log-scale of positive amounts (amount donated conditional on donating).
*   **std_error_zero**: (float) Standard error for zero-inflation coefficient.
*   **std_error_gamma**: (float) Standard error for gamma coefficient.
*   **p_value_zero**: (float) P-value for zero-inflation component.
*   **p_value_gamma**: (float) P-value for gamma component.
*   **ci_lower_zero**: (float) 95% CI lower bound for zero-inflation.
*   **ci_upper_zero**: (float) 95% CI upper bound for zero-inflation.
*   **ci_lower_gamma**: (float) 95% CI lower bound for gamma component.
*   **ci_upper_gamma**: (float) 95% CI upper bound for gamma component.
*   **n_samples**: (integer) Total N used.
*   **n_zeros**: (integer) Count of zero outcomes.
*   **sensitivity_sweep**: (list) Results from sensitivity analysis (link function/distribution sweep).
*   **power_analysis**: (object) Meta-analytic power assessment results (MDES, power).

## Data Flow

1.  **Ingestion**: Raw files -> `Dataset` (validation) -> `Participant` (raw).
2.  **Preprocessing**: `Participant` (raw) -> Imputation/Filtering -> `Participant` (clean).
3.  **Pooling**: `Participant` (clean) filtered by `randomized` -> `Causal Pool` / `Associational Pool`.
4.  **Analysis**: Pools -> Model Fit -> `AnalysisResult` (dual components).
5.  **Aggregation**: Multiple `AnalysisResult` -> Meta-analysis -> Final Report.