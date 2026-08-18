# Analysis Module API Documentation

This document provides the API reference for the `code/analysis.py` module, which implements the statistical modeling and validation logic for the Physical Activity and Mood Variability study.

## Module Overview

The `analysis` module handles:
- Loading and validating daily aggregate data
- Fitting Linear Mixed-Effects Models (LMM) for mood variability and mean mood
- Enforcing transformation constraints (log-transform with epsilon offset)
- Running Leave-One-Participant-Out (LOPO) cross-validation
- Performing sensitivity analyses (weekdays, active minutes, single-rating handling)
- Extracting model coefficients and diagnostics

## Functions

### `load_daily_aggregates()`

Loads the daily aggregates dataset from disk.

**Returns:**
- `pd.DataFrame`: The daily aggregates dataframe containing participant-day level data.

**Raises:**
- `FileNotFoundError`: If `data/processed/daily_aggregates.csv` does not exist.

**Path:**
- Reads from: `data/processed/daily_aggregates.csv`

---

### `validate_raw_mood_std()`

Validates that the `mood_std` column in the daily aggregates contains no negative values or NaNs.

**Returns:**
- `bool`: `True` if validation passes, `False` otherwise.

**Side Effects:**
- Logs validation results to the module logger.

**Precondition:**
- Requires `daily_aggregates.csv` to exist and be loadable.

---

### `enforce_transform_constraint()`

A decorator/wrapper that enforces the global constraint: "No code path may use `mood_std` directly in a log calculation without the epsilon offset of a small magnitude."

**Usage:**
- Applied to `fit_lmm_variability` and `fit_lmm_mean` to ensure the transformation `np.log(mood_std + 0.01)` is applied correctly.

**Parameters:**
- `func`: The function to wrap.

**Returns:**
- Wrapped function that applies the transformation constraint.

---

### `fit_lmm_variability()`

Fits the primary Linear Mixed-Effects Model (LMM) to test the association between physical activity and mood variability.

**Model Specification:**
- **Outcome:** `log(mood_std + 0.01)`
- **Fixed Effects:** `total_steps`, `sleep_duration`, `baseline_affect`, `day_of_week`
- **Random Effects:** Random intercepts for `participant_id`

**Parameters:**
- `data` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `dict`: Model results including fixed effects, random effects, and fit statistics.

**Note:**
- This function invokes `enforce_transform_constraint()` to apply the log transformation.

---

### `fit_lmm_mean()`

Fits the secondary Linear Mixed-Effects Model (LMM) to test the association between physical activity and mean mood.

**Model Specification:**
- **Outcome:** `mean_mood`
- **Fixed Effects:** `total_steps`, `sleep_duration`, `baseline_affect`, `day_of_week`
- **Random Effects:** Random intercepts for `participant_id`

**Parameters:**
- `data` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `dict`: Model results including fixed effects, random effects, and fit statistics.

---

### `extract_model_coefficients()`

Extracts fixed-effect coefficients, standard errors, p-values, and 95% confidence intervals from fitted LMM models.

**Parameters:**
- `model_results` (dict): The dictionary of model results from `fit_lmm_variability` or `fit_lmm_mean`.

**Returns:**
- `dict`: A structured dictionary of coefficients for `total_steps` and covariates.

---

### `run_model_diagnostics()`

Performs model diagnostics including Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests.

**Parameters:**
- `model` (statsmodels mixedlm.MixedLMResults): The fitted model object.

**Returns:**
- `dict`: Diagnostic test results and p-values.

**Side Effects:**
- Generates residual plots ('residuals vs. fitted') and saves them to `data/processed/`.

---

### `run_lopo_cv()`

Runs Leave-One-Participant-Out (LOPO) cross-validation to assess model robustness.

**Process:**
- Retrains the primary model N times (where N = number of participants).
- Tracks the sign stability of the `total_steps` coefficient.
- Calculates the average RMSE across all folds.

**Parameters:**
- `data` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `dict`: LOPO results including sign consistency percentage and average RMSE.

---

### `run_sensitivity_weekdays()`

Runs the primary model on a "weekdays only" subset of the data to test sensitivity to weekend effects.

**Parameters:**
- `data` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `dict`: Comparison of coefficients with the full-sample model.

---

### `run_sensitivity_active_minutes()`

Runs the primary model using "active minutes" instead of step counts to test sensitivity to the activity metric.

**Parameters:**
- `data` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `dict`: Comparison of effect direction with the step-count model.

---

### `run_sensitivity_single_rating_bootstrap()`

Executes a bootstrap sampling loop (1000 iterations, seed 42) to assess the robustness of results when handling single-rating days.

**Process:**
- For each iteration:
 1. Fit the exclusion model (days with single ratings removed).
 2. Fit the imputation model (single ratings imputed with participant median).
 3. Compare coefficients to check direction consistency.
- Calculates the percentage of iterations where the direction remains consistent.

**Parameters:**
- `data` (pd.DataFrame): The daily aggregates dataset.

**Returns:**
- `dict`: Bootstrap consistency percentage and pass/fail status (threshold ≥80%).

---

### `run_analysis()`

Orchestrates the full analysis pipeline: data loading, model fitting, diagnostics, validation, and sensitivity checks.

**Returns:**
- `dict`: Aggregated results including model coefficients, diagnostics, LOPO, and sensitivity analysis.

**Side Effects:**
- Writes `data/processed/model_results.json`.

---

### `main()`

Entry point for running the analysis script.

**Usage:**
```bash
python code/analysis.py
```

**Side Effects:**
- Executes `run_analysis()` and prints summary results.
- Writes `data/processed/model_results.json`.

## Dependencies

- `pandas`
- `statsmodels`
- `numpy`
- `scipy`
- `matplotlib` (for diagnostic plots)
- `config` (for path utilities)

## Notes

- All results are explicitly labeled as "associational" to comply with FR-004.
- The `mood_std` transformation uses a fixed epsilon of `0.01` to handle zero variability.
- LOPO cross-validation flags results if sign consistency is below 90% but continues execution.
- Sensitivity analysis for single-rating handling requires a consistency of ≥80% to pass.
