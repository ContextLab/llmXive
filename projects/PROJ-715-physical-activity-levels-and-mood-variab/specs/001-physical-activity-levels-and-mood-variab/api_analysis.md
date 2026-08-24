# API Documentation: `code/analysis.py`

This module implements the statistical modeling and validation pipeline for the
Physical Activity Levels and Mood Variability project. It fits Linear Mixed-Effects
Models (LMM) to test associations between physical activity and mood metrics,
performs rigorous diagnostics, and executes sensitivity analyses.

## Imports

```python
import os
import sys
import logging
import json
import random
import numpy as np
```

## Public Functions

### `load_daily_aggregates()`
Loads the preprocessed daily aggregates from `data/processed/daily_aggregates.csv`.
- **Returns**: `pandas.DataFrame` containing daily aggregates.
- **Raises**: `FileNotFoundError` if the file does not exist.

### `load_model_results()`
Loads the model results from `data/processed/model_results.json`.
- **Returns**: `dict` containing model results.
- **Raises**: `FileNotFoundError` if the file does not exist.

### `save_model_results(results: dict, path: str)`
Saves the model results dictionary to a JSON file.
- **Parameters**:
 - `results`: The dictionary of results to save.
 - `path`: The output file path.

### `validate_raw_mood_std(df: pd.DataFrame)`
Validates that the `mood_std` column in the provided DataFrame contains no negative
values or NaNs.
- **Parameters**:
 - `df`: The DataFrame to validate.
- **Raises**: `ValueError` if validation fails.

### `apply_log_transform(mood_std: np.ndarray) -> np.ndarray`
Applies a log transformation to the mood standard deviation array.
- **Parameters**:
 - `mood_std`: The array of mood standard deviations.
- **Returns**: The log-transformed array (`np.log(mood_std + epsilon)`).

### `fit_lmm_variability(df: pd.DataFrame)`
Fits the primary Linear Mixed-Effects Model with log-transformed `mood_std` as the
outcome and `total_steps` as the primary predictor.
- **Parameters**:
 - `df`: The input DataFrame with daily aggregates.
- **Returns**: The fitted model object.

### `fit_lmm_mean(df: pd.DataFrame)`
Fits the secondary Linear Mixed-Effects Model with `mean_mood` as the outcome and
`total_steps` as the predictor.
- **Parameters**:
 - `df`: The input DataFrame with daily aggregates.
- **Returns**: The fitted model object.

### `extract_model_coefficients(models: dict)`
Extracts fixed-effect coefficients, standard errors, p-values, and 95% CIs for
`total_steps` and covariates from both models.
- **Parameters**:
 - `models`: A dictionary containing the fitted models.
- **Returns**: A dictionary of extracted coefficients.

### `run_model_diagnostics(models: dict)`
Performs model diagnostics (Shapiro-Wilk, Breusch-Pagan) and generates residual
plots (specifically "residuals vs. fitted").
- **Parameters**:
 - `models`: A dictionary containing the fitted models.
- **Returns**: A dictionary of diagnostic results.

### `run_lopo_cv(df: pd.DataFrame, models: dict)`
Performs Leave-One-Participant-Out (LOPO) cross-validation. Retrains the primary
model N times (N = number of participants), tracks `total_steps` coefficient sign
stability, and calculates the average RMSE across all folds.
- **Parameters**:
 - `df`: The input DataFrame.
 - `models`: The primary model to retrain.
- **Returns**: A dictionary with `average_rmse` and `sign_consistency_pct`.

### `run_sensitivity_weekdays(df: pd.DataFrame, primary_model)`
Re-runs the primary model on "weekdays only" data and compares coefficients.
- **Parameters**:
 - `df`: The input DataFrame.
 - `primary_model`: The primary model template.
- **Returns**: A dictionary with `sign_consistent` and `pvalue_consistent` flags.

### `run_sensitivity_active_minutes(df: pd.DataFrame, primary_model)`
Re-runs the model using "active minutes" instead of step counts and compares
the direction of effect.
- **Parameters**:
 - `df`: The input DataFrame.
 - `primary_model`: The primary model template.
- **Returns**: A dictionary with the comparison result.

### `run_sensitivity_single_rating_bootstrap(df: pd.DataFrame)`
Executes a bootstrap sampling loop (config.BOOTSTRAP_ITERATIONS iterations) to
compare exclusion vs. imputation models for single-rating days.
- **Parameters**:
 - `df`: The input DataFrame.
- **Returns**: A dictionary with `consistency_pct` and `pass` (boolean).

### `append_lopo_and_sensitivity_results(base_results: dict, lopo_results: dict, sensitivity_results: dict)`
Merges base model results with LOPO and sensitivity analysis outputs into a single
dictionary matching `model_results.schema.yaml`.
- **Parameters**:
 - `base_results`: The base model results.
 - `lopo_results`: The LOPO cross-validation results.
 - `sensitivity_results`: The sensitivity analysis results.
- **Returns**: The merged results dictionary.

### `validate_against_schema(results: dict, schema_path: str)`
Validates the results dictionary against the provided YAML schema.
- **Parameters**:
 - `results`: The results dictionary.
 - `schema_path`: Path to the schema file.
- **Raises**: `ValidationError` if the schema does not match.

### `run_analysis(input_path: str, output_path: str)`
Orchestrates the full analysis pipeline: loading data, validating, fitting models,
running diagnostics, and saving results.
- **Parameters**:
 - `input_path`: Path to `daily_aggregates.csv`.
 - `output_path`: Path for `model_results.json`.

### `main()`
Entry point for the script. Parses arguments and calls `run_analysis()`.

## Dependencies

- `pandas`
- `statsmodels`
- `numpy`
- `scikit-learn` (for diagnostics)
- `yaml` (for schema validation)
