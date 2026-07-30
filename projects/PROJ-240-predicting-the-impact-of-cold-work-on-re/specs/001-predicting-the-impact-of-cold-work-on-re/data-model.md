# Data Model: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

## Entity Definitions

### 1. ExperimentRecord
Represents a single experimental data point (raw or synthetic).
- **cold_work_pct**: float (0.0 to 100.0) - Percentage of cold work deformation.
- **mg_wt**: float (0.0 to 5.0) - Magnesium weight percentage.
- **si_wt**: float (0.0 to 1.5) - Silicon weight percentage.
- **cu_wt**: float (0.0 to 4.0) - Copper weight percentage.
- **mn_wt**: float (0.0 to 1.5) - Manganese weight percentage.
- **annealing_temp_k**: float (300.0 to 600.0) - Annealing temperature in Kelvin.
- **time_to_peak_min**: float (>0) - Observed time to peak softening in minutes.
- **source**: string - "synthetic" or "public".
- **row_id**: string - Unique identifier (UUID or hash).

### 2. EngineeredFeatureSet
Derived dataset used for model training. Extends `ExperimentRecord` with:
- **interaction_cw_mg**: float - `cold_work_pct` * `mg_wt`
- **interaction_cw_si**: float - `cold_work_pct` * `si_wt`
- **interaction_cw_cu**: float - `cold_work_pct` * `cu_wt`
- **interaction_cw_mn**: float - `cold_work_pct` * `mn_wt`
- **is_outlier_clipped**: boolean - True if original `time_to_peak_min` was > 99th percentile.

### 3. ModelPerformanceMetrics
Aggregated results from training and testing.
- **r2_score**: float - Coefficient of determination on test set.
- **mae**: float - Mean Absolute Error on test set.
- **cv_r2_mean**: float - Mean R² from 5-fold cross-validation.
- **cv_r2_std**: float - Standard deviation of R² from 5-fold cross-validation.
- **permutation_p_value**: float - P-value from the Delta-Permutation Test (Additive vs. Interaction).
- **shap_top_features**: list[string] - Top 5 feature names by Shapley value.
- **timestamp**: string - ISO 8601 timestamp of generation.

## Data Flow

1. **Ingestion**: `generate_synthetic.py` -> `raw_synthetic.csv`
2. **Cleaning**: `ingest.py` (imputation, outlier clipping) -> `cleaned_data.csv`
3. **Engineering**: `engineer.py` (interaction terms) -> `engineered_features.csv`
4. **Modeling**: `train.py` -> `model.pkl`, `metrics.json`
5. **Analysis**: `evaluate.py` -> `shap_summary.json`, `permutation_test.json`

## Constraints & Validation Rules

- **Null Handling**: No null values allowed in predictor columns. Rows with missing composition data must be imputed (mean) or dropped.
- **Range Checks**:
  - `cold_work_pct`: [0, 100]
  - `time_to_peak_min`: > 0
- **Minimum Size**: Dataset must have >= 50 rows before training (FR-008).
- **Outlier Clipping**: Values > 99th percentile of `time_to_peak_min` must be capped and flagged.
- **Sample Size**: Dataset must have >= 500 rows to ensure statistical power for the permutation test (Research Plan).