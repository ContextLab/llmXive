# Data Model: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

## 1. Entities & Relationships

### 1.1 Dataset
Represents a single study from an external source.
-   `id`: Unique identifier (UUID or hash).
-   `source_url`: Original URL (OSF/HuggingFace).
-   `raw_columns`: List of original column names.
-   `is_valid`: Boolean (true if schema passes FR-001.5).
-   `is_randomized`: Boolean (from `randomized` flag).
-   `exclusion_n`: Integer (count of participants in exclusion condition).
-   `inclusion_n`: Integer (count of participants in inclusion condition).
-   `missing_rate`: Float (percentage of NaN in `prosocial_amount`).
-   `mapping_log`: JSON object storing the exact mapping logic (e.g., `{"raw_value": "ignored", "mapped_value": 1}`).

### 1.2 Participant
Represents a single row in the standardized dataset.
-   `dataset_id`: FK to Dataset.
-   `condition`: Integer (0=Included, 1=Excluded).
-   `prosocial_amount`: Float (Continuous donation amount or 0).
-   `outcome_type`: String ("continuous" or "binary").
-   `is_outlier`: Boolean (True if >3 SD from mean).
-   `task_timestamp`: String/Float (Optional, used to validate temporal separation per Principle VII).

### 1.3 AnalysisResult
Represents the output of a single regression model and meta-analytic summary.
-   `dataset_id`: FK to Dataset.
-   `pool_type`: String ("Causal" or "Associational").
-   `model_type`: String ("ZIG", "Hurdle", "Logistic").
-   **Marginal Effects**:
    -   `expected_donation_included`: Float (E[Y|X=0]).
    -   `expected_donation_excluded`: Float (E[Y|X=1]).
    -   `ame_total_effect`: Float (Difference: Excluded - Included).
    -   `ame_se`: Float (Standard error of AME).
    -   `ame_p`: Float (P-value of AME).
    -   `ame_ci_lower`: Float.
    -   `ame_ci_upper`: Float.
-   **Component Diagnostics** (for internal use, not primary pooling):
    -   `zero_inflation_coeff`: Float (Log-odds for zero process).
    -   `positive_amount_coeff`: Float (Log-scale for positive process).
-   **Robustness Metrics**:
    -   `e_value`: Float (For Associational Pool).
    -   `is_bias_adjusted`: Boolean (True if Trim-and-Fill was applied).
    -   `adjusted_ame`: Float (AME after small-sample bias correction).

## 2. Data Flow

1.  **Raw Ingestion**: Download CSV/Parquet -> Validate Schema -> Store in `data/raw/`.
2.  **Standardization**: Map columns -> **Log Mapping Logic** -> Impute NaN (if <5%) -> Flag structural zeros -> Store in `data/processed/standardized.csv`.
3.  **Filtering**: Remove datasets with `exclusion_n < 5` -> Store in `data/processed/filtered.csv`.
4.  **Splitting**: Split into `Causal` and `Associational` subsets.
5.  **Model Fitting**: Run ZIG/Hurdle -> Calculate **AME** -> Store `AnalysisResult` in `data/processed/results.csv`.
6.  **Meta-Analysis**: Aggregate AME -> Apply **Trim-and-Fill** -> Store pooled estimates in `data/processed/meta_analysis.json`.

## 3. Schema Constraints

-   `prosocial_amount`: Must be non-negative.
-   `condition`: Must be binary (0 or 1).
-   `randomized`: Must be boolean or null (treated as false).
- `missing_rate`: Threshold for imputation is 0.05.
-   `exclusion_n`: Threshold for inclusion is 5.
-   `mapping_log`: Must be a valid JSON object recording the transformation.