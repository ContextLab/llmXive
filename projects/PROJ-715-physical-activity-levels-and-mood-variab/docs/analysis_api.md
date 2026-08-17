# Analysis Module API Documentation

The `code/analysis.py` module provides the core statistical modeling, validation, and sensitivity analysis functionality for the Physical Activity and Mood Variability study. It implements Linear Mixed-Effects Models (LMM) to test associations between physical activity levels and mood metrics.

## Dependencies

- `pandas`: Data manipulation
- `statsmodels`: Statistical modeling (LMM)
- `scipy`: Statistical tests (Shapiro-Wilk, Breusch-Pagan)
- `numpy`: Numerical operations
- `matplotlib`: Plotting (for diagnostics)

## Functions

### `load_daily_aggregates() -> pd.DataFrame`

Loads the preprocessed daily aggregates dataset.

**Returns:**
- `pd.DataFrame`: Contains columns `participant_id`, `date`, `total_steps`, `mean_mood`, `mood_std` (log-transformed), `sleep_duration`, `baseline_affect`, and `day_of_week`.

**Notes:**
- The `mood_std` column is already log-transformed as `np.log(mood_std + 0.01)` by the preprocessing step (T015b).
- Uses `config.get_path` to locate `data/processed/daily_aggregates.csv`.

---

### `fit_mood_std_model(df: pd.DataFrame) -> statsmodels.regression.mixed_linear_model.MixedLMResults`

Fits a Linear Mixed-Effects Model with log-transformed mood variability as the outcome.

**Formula:**
`mood_std ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect`

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `MixedLMResults`: The fitted model object containing coefficients, standard errors, and p-values.

**Random Effects:**
- Random intercepts for `participant_id` to account for within-subject correlation.

---

### `fit_mean_mood_model(df: pd.DataFrame) -> statsmodels.regression.mixed_linear_model.MixedLMResults`

Fits a Linear Mixed-Effects Model with mean mood as the outcome.

**Formula:**
`mean_mood ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect`

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `MixedLMResults`: The fitted model object.

**Note:**
- This model is considered secondary to the `mood_std` model.

---

### `extract_coefficient(model_results, variable_name: str) -> dict`

Extracts fixed-effect statistics for a specific predictor variable.

**Parameters:**
- `model_results`: The fitted model object.
- `variable_name` (str): The name of the predictor (e.g., `'total_steps'`).

**Returns:**
- `dict`: Contains `estimate`, `std_err`, `p_value`, and `ci_95` (lower, upper).

---

### `run_model_diagnostics(model_results) -> dict`

Performs residual diagnostics on the fitted model.

**Tests Performed:**
- **Shapiro-Wilk Test**: Checks for normality of residuals.
- **Breusch-Pagan Test**: Checks for heteroscedasticity.

**Returns:**
- `dict`: Contains test statistics, p-values, and a `residuals_vs_fitted` plot path.

---

### `run_lopo_validation(df: pd.DataFrame) -> dict`

Performs Leave-One-Participant-Out (LOPO) cross-validation.

**Logic:**
1. Iterates through each participant, excluding them from the training set.
2. Fits the primary model on the remaining data.
3. Records the coefficient sign and RMSE for the excluded participant's data.
4. Aggregates results to calculate sign consistency and average RMSE.

**Returns:**
- `dict`: Contains `lopo_average_rmse`, `sign_consistency_percentage`, and a flag indicating if consistency is >= 90%.

---

### `run_sensitivity_analysis_exclude_single_ratings(df: pd.DataFrame) -> dict`

Re-runs the primary model excluding days with only a single mood rating.

**Returns:**
- `dict`: Contains model coefficients and comparison to the full dataset model.

---

### `run_sensitivity_analysis_impute_single_ratings(df: pd.DataFrame) -> dict`

Re-runs the primary model imputing single-rating days with the participant's median mood.

**Returns:**
- `dict`: Contains model coefficients and comparison to the full dataset model.

---

### `run_bootstrap_sensitivity_analysis(df: pd.DataFrame, n_iterations: int = 1000, seed: int = 42) -> dict`

Performs bootstrap sampling to assess the robustness of the single-rating handling.

**Logic:**
1. For each iteration:
 - Sample the dataset with replacement.
 - Fit the exclusion model (T031a) and imputation model (T031b).
 - Compare the direction (sign) of the `total_steps` coefficient.
2. Calculate the percentage of iterations where the direction is consistent.

**Returns:**
- `dict`: Contains `bootstrap_consistency_percentage` and a flag indicating if consistency is >= 80%.

---

### `run_analysis(df: pd.DataFrame) -> dict`

Orchestrates the full analysis pipeline.

**Steps:**
1. Fits the primary (`mood_std`) and secondary (`mean_mood`) models.
2. Extracts coefficients and diagnostics.
3. Runs LOPO validation.
4. Runs sensitivity analyses.
5. Runs bootstrap sensitivity analysis.

**Returns:**
- `dict`: A comprehensive dictionary containing all results, ready for serialization to `model_results.json`.

---

### `run_sensitivity_analysis_exclude_single_ratings(df: pd.DataFrame) -> dict`

(See specific function documentation above).

---

### `run_sensitivity_analysis_impute_single_ratings(df: pd.DataFrame) -> dict`

(See specific function documentation above).

---

### `main()`

Entry point for the analysis script.

**Workflow:**
1. Loads `daily_aggregates.csv`.
2. Calls `run_analysis()`.
3. Validates the results against `model_results.schema.yaml`.
4. Saves the results to `data/processed/model_results.json`.

## Error Handling

- The module raises `ValueError` if the input DataFrame is missing required columns.
- Model fitting failures (non-convergence) raise `RuntimeError` with details.
- All statistical tests check for valid p-values and raise warnings if assumptions are violated.
