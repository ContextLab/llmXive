# Analysis Module API Documentation

This document describes the public API for the `code/analysis.py` module, which handles statistical modeling, validation, and sensitivity analysis for the physical activity and mood variability study.

## Overview

The `analysis.py` module provides functions to:
1. Load and validate daily aggregate data
2. Fit Linear Mixed-Effects Models (LMM) for mood variability and mean mood
3. Extract model coefficients and diagnostics
4. Perform Leave-One-Participant-Out (LOPO) cross-validation
5. Run sensitivity analyses (weekdays-only, active minutes, single-rating bootstrap)
6. Save and validate model results against schema

## Functions

### `load_daily_aggregates()`
Loads the preprocessed daily aggregates dataset.

**Returns:**
- `pd.DataFrame`: The daily aggregates DataFrame containing columns: `participant_id`, `date`, `total_steps`, `mean_mood`, `mood_std`, `n_mood_ratings`, `sleep_duration`, `baseline_affect`, `day_of_week`.

**Raises:**
- `FileNotFoundError`: If `data/processed/daily_aggregates.csv` does not exist.

---

### `load_model_results()`
Loads the model results JSON file.

**Returns:**
- `dict`: The model results dictionary containing fixed effects, random effects, model fit statistics, validation metrics, and sensitivity analysis results.

**Raises:**
- `FileNotFoundError`: If `data/processed/model_results.json` does not exist.
- `json.JSONDecodeError`: If the file is not valid JSON.

---

### `save_model_results(results: dict, output_path: str = None)`
Saves the model results dictionary to a JSON file.

**Parameters:**
- `results` (dict): The model results dictionary to save.
- `output_path` (str, optional): Path to save the JSON file. Defaults to `data/processed/model_results.json`.

**Returns:**
- `str`: The path where the results were saved.

---

### `validate_raw_mood_std()`
Validates that the `mood_std` column in `daily_aggregates.csv` contains no negative values or NaNs.

**Returns:**
- `bool`: `True` if validation passes, `False` otherwise.

**Raises:**
- `AssertionError`: If `mood_std` contains negative values or NaNs.

---

### `apply_log_transform(mood_std: np.ndarray) -> np.ndarray`
Applies the log transformation to mood standard deviation values.

**Parameters:**
- `mood_std` (np.ndarray): Array of mood standard deviation values.

**Returns:**
- `np.ndarray`: Transformed values using `np.log(mood_std + 0.01)`.

**Note:**
This is the **SINGLE authorized mechanism** for log transformation in the pipeline. The `+ 0.01` offset is hardcoded here to ensure deterministic compliance with FR-003.

---

### `fit_lmm_variability(df: pd.DataFrame) -> dict`
Fits the primary Linear Mixed-Effects Model with log-transformed `mood_std` as the outcome and `total_steps` as the primary predictor.

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates DataFrame.

**Returns:**
- `dict`: Model results including fixed effects, random effects, and model fit statistics.

**Model Formula:**
```
log(mood_std + 0.01) ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect + (1 | participant_id)
```

---

### `fit_lmm_mean(df: pd.DataFrame) -> dict`
Fits the secondary Linear Mixed-Effects Model with `mean_mood` as the outcome and `total_steps` as the predictor.

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates DataFrame.

**Returns:**
- `dict`: Model results including fixed effects, random effects, and model fit statistics.

**Model Formula:**
```
mean_mood ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect + (1 | participant_id)
```

---

### `extract_model_coefficients(model_results: dict, model_type: str) -> dict`
Extracts fixed-effect coefficients, standard errors, p-values, and 95% CIs from model results.

**Parameters:**
- `model_results` (dict): The model results dictionary.
- `model_type` (str): The type of model ('variability' or 'mean').

**Returns:**
- `dict`: Extracted coefficients for all predictors including `total_steps` and covariates.

---

### `run_model_diagnostics(model, residuals: np.ndarray, fitted: np.ndarray) -> dict`
Performs model diagnostics including Shapiro-Wilk test for normality and Breusch-Pagan test for homoscedasticity.

**Parameters:**
- `model`: The fitted model object.
- `residuals` (np.ndarray): Model residuals.
- `fitted` (np.ndarray): Fitted values.

**Returns:**
- `dict`: Diagnostic results including test statistics, p-values, and plot paths.

**Diagnostics Performed:**
- Shapiro-Wilk test for normality of residuals
- Breusch-Pagan test for heteroscedasticity
- Residuals vs. fitted plot generation

---

### `run_lopo_cv(df: pd.DataFrame, model_func) -> dict`
Runs Leave-One-Participant-Out cross-validation.

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates DataFrame.
- `model_func` (callable): The model fitting function to use.

**Returns:**
- `dict`: LOPO results including average RMSE and sign consistency percentage.

**Output Keys:**
- `lopo_average_rmse`: Average RMSE across all LOPO folds.
- `lopo_sign_consistency_pct`: Percentage of folds where the `total_steps` coefficient sign matches the full model.

---

### `run_sensitivity_weekdays(df: pd.DataFrame) -> dict`
Runs sensitivity analysis on weekdays-only dataset.

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates DataFrame.

**Returns:**
- `dict`: Sensitivity results comparing coefficients to the full model.

**Output Keys:**
- `weekdays_only_sign_consistent`: Boolean indicating if the coefficient direction matches the full model.

---

### `run_sensitivity_active_minutes(df: pd.DataFrame) -> dict`
Runs sensitivity analysis using "active minutes" instead of step counts.

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates DataFrame.

**Returns:**
- `dict`: Sensitivity results comparing the direction of effect.

**Output Keys:**
- `active_minutes_sign_consistent`: Boolean indicating if the coefficient direction matches the full model.

---

### `run_sensitivity_single_rating_bootstrap(df: pd.DataFrame, n_iterations: int = None) -> dict`
Runs bootstrap sampling to test consistency between exclusion and imputation models for single-rating days.

**Parameters:**
- `df` (pd.DataFrame): The daily aggregates DataFrame.
- `n_iterations` (int, optional): Number of bootstrap iterations. Defaults to `config.BOOTSTRAP_ITERATIONS` (1000).

**Returns:**
- `dict`: Bootstrap consistency results.

**Output Keys:**
- `single_rating_bootstrap_consistency`: Percentage of iterations where the coefficient sign matches between exclusion and imputation models.
- `single_rating_bootstrap_pass`: Boolean indicating if consistency >= 80%.

---

### `append_lopo_and_sensitivity_results(results: dict, lopo_results: dict, sensitivity_results: dict)`
Appends LOPO and sensitivity analysis results to the base model results dictionary.

**Parameters:**
- `results` (dict): The base model results dictionary.
- `lopo_results` (dict): LOPO cross-validation results.
- `sensitivity_results` (dict): Sensitivity analysis results.

**Updates:**
- `results['validation']` with LOPO metrics
- `results['sensitivity']` with sensitivity metrics

---

### `validate_against_schema(data: dict, schema_path: str) -> bool`
Validates data against a YAML schema.

**Parameters:**
- `data` (dict): The data to validate.
- `schema_path` (str): Path to the schema YAML file.

**Returns:**
- `bool`: `True` if validation passes, `False` otherwise.

---

### `run_analysis()`
Main entry point for running the full analysis pipeline.

**Steps:**
1. Load daily aggregates
2. Validate `mood_std` values
3. Fit LMM for variability and mean mood
4. Extract coefficients and run diagnostics
5. Perform LOPO cross-validation
6. Run sensitivity analyses
7. Append all results and save to JSON

**Returns:**
- `str`: Path to the saved `model_results.json` file.

---

### `main()`
Command-line entry point. Executes `run_analysis()` and logs the output path.

**Usage:**
```bash
python code/analysis.py
```

## Dependencies

- `pandas`: Data manipulation
- `statsmodels`: Linear mixed-effects modeling
- `numpy`: Numerical operations
- `scipy`: Statistical tests (Shapiro-Wilk, Breusch-Pagan)
- `config`: Project configuration and path utilities

## Notes

- All models are labeled as "associational" in internal data structures to comply with FR-004.
- The log transformation offset (`+ 0.01`) is applied ONLY in `apply_log_transform()` to ensure deterministic behavior.
- LOPO and sensitivity analyses continue execution even if consistency thresholds are not met, flagging results in the output JSON.
