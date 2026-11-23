# API Documentation: `code/analysis.py`

## Overview
This module implements the statistical modeling and validation pipeline for the
"Physical Activity Levels and Mood Variability" study. It fits Linear Mixed-Effects
Models (LMM) to test associations between physical activity (step counts) and mood
metrics, performs diagnostics, and conducts sensitivity analyses.

## Dependencies
- `pandas`
- `statsmodels`
- `scikit-learn` (for LOPO splitting)
- `numpy`
- `json`
- `logging`

## Public Functions

### `load_daily_aggregates(filepath: str) -> pd.DataFrame`
Loads the preprocessed daily aggregates dataset.
- **Args**:
 - `filepath`: Path to the `daily_aggregates.csv` file.
- **Returns**: A pandas DataFrame containing the aggregated data.
- **Side Effects**: Logs loading status.

### `fit_mood_std_model(df: pd.DataFrame) -> statsmodels.regression.mixed_linear.MixedLMResults`
Fits a Linear Mixed-Effects Model with `log(mood_std + 0.01)` as the outcome
and `total_steps` as the primary predictor.
- **Formula**: `log_mood_std ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect`
- **Random Effects**: Random intercepts for `participant_id`.
- **Args**:
 - `df`: DataFrame containing the daily aggregates.
- **Returns**: Fitted model results object.

### `fit_mean_mood_model(df: pd.DataFrame) -> statsmodels.regression.mixed_linear.MixedLMResults`
Fits a Linear Mixed-Effects Model with `mean_mood` as the outcome.
- **Formula**: `mean_mood ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect`
- **Random Effects**: Random intercepts for `participant_id`.
- **Args**:
 - `df`: DataFrame containing the daily aggregates.
- **Returns**: Fitted model results object.

### `extract_coefficient(results: MixedLMResults, param_name: str) -> dict`
Extracts fixed-effect statistics for a specific parameter.
- **Args**:
 - `results`: Fitted model results.
 - `param_name`: Name of the parameter (e.g., `total_steps`).
- **Returns**: Dictionary with keys: `estimate`, `std_err`, `p_value`, `ci_lower`, `ci_upper`.

### `run_model_diagnostics(results: MixedLMResults, df: pd.DataFrame, plot_path: str) -> dict`
Performs residual diagnostics and generates plots.
- **Tests**: Shapiro-Wilk (normality), Breusch-Pagan (heteroscedasticity).
- **Plots**: 'residuals vs. fitted' saved to `plot_path`.
- **Returns**: Dictionary of test statistics and p-values.

### `run_lopo_validation(df: pd.DataFrame, n_splits: int = None) -> dict`
Performs Leave-One-Participant-Out (LOPO) cross-validation.
- **Logic**: Iteratively fits the model leaving out one participant, tracks coefficient sign
 stability and RMSE.
- **Returns**: Dictionary containing `sign_consistency_pct`, `average_rmse`, and `fold_results`.

### `run_sensitivity_analysis_exclude_single_ratings(df: pd.DataFrame) -> dict`
Re-runs the primary model excluding days with only a single mood rating.
- **Returns**: Model results and comparison metrics against the full dataset.

### `run_sensitivity_analysis_impute_single_ratings(df: pd.DataFrame) -> dict`
Re-runs the primary model imputing missing ratings for single-rating days
using the participant's median mood.
- **Returns**: Model results and comparison metrics.

### `run_bootstrap_sensitivity_analysis(df: pd.DataFrame, n_iterations: int = 1000, seed: int = 42) -> dict`
Performs bootstrap sampling to assess the robustness of the single-rating handling.
- **Logic**: Compares coefficients between the exclusion and imputation models
 across iterations.
- **Returns**: Dictionary with `consistency_percentage` and `threshold_met` (≥80%).

### `run_analysis(df: pd.DataFrame, output_path: str) -> dict`
Orchestrates the full analysis pipeline:
1. Fits both `mood_std` and `mean_mood` models.
2. Extracts coefficients.
3. Runs diagnostics.
4. Runs LOPO validation.
5. Runs sensitivity analyses.
6. Saves results to `output_path`.
- **Returns**: Dictionary containing all results.

### `main()`
Entry point for the script. Loads data from `data/processed/daily_aggregates.csv`,
runs the analysis, and saves results to `data/processed/model_results.json`.

## Usage Example
```python
from analysis import run_analysis

results = run_analysis(
 df_path="data/processed/daily_aggregates.csv",
 output_path="data/processed/model_results.json"
)
print(f"Sign Consistency: {results['validation']['lopo_sign_consistency_pct']}%")
```
