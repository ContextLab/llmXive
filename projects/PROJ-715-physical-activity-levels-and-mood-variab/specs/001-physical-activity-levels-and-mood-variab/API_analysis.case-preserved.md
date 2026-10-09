# Analysis Module API Documentation

This document describes the public API of `code/analysis.py`, which implements the statistical modeling and validation logic for the Physical Activity Levels and Mood Variability project.

## Overview

The `analysis.py` module provides functions to:
- Load and validate daily aggregate data
- Apply log transformations to mood variability metrics
- Fit Linear Mixed-Effects Models (LMM) for mood variability and mean mood
- Extract model coefficients and diagnostics
- Perform Leave-One-Participant-Out (LOPO) cross-validation
- Conduct sensitivity analyses (weekdays-only, active minutes, single-rating handling)
- Save and validate results against schema contracts

## Functions

### `load_daily_aggregates() -> pd.DataFrame`

Loads the preprocessed daily aggregates from disk.

**Returns**:
- `pd.DataFrame`: The daily aggregates dataset containing `participant_id`, `date`, `total_steps`, `mean_mood`, `mood_std`, etc.

**Raises**:
- `FileNotFoundError`: If `data/processed/daily_aggregates.csv` does not exist.

---

### `load_model_results() -> dict`

Loads the final model results from disk.

**Returns**:
- `dict`: The model results dictionary conforming to `model_results.schema.yaml`.

**Raises**:
- `FileNotFoundError`: If `data/processed/model_results.json` does not exist.

---

### `save_model_results(results: dict, path: str = None) -> None`

Saves the model results dictionary to a JSON file.

**Parameters**:
- `results` (dict): The results dictionary to save.
- `path` (str, optional): Output file path. Defaults to `data/processed/model_results.json`.

---

### `validate_raw_mood_std(df: pd.DataFrame) -> None`

Validates that the `mood_std` column in the daily aggregates contains no negative values or NaNs.

**Parameters**:
- `df` (pd.DataFrame): The daily aggregates DataFrame.

**Raises**:
- `ValueError`: If negative values or NaNs are found in `mood_std`.

---

### `apply_log_transform(mood_std: np.ndarray) -> np.ndarray`

Applies a log transformation to the mood standard deviation array.

**Parameters**:
- `mood_std` (np.ndarray): Array of mood standard deviation values.

**Returns**:
- `np.ndarray`: Log-transformed values using `np.log(mood_std + epsilon)`.

---

### `fit_lmm_variability(df: pd.DataFrame) -> object`

Fits the primary Linear Mixed-Effects Model for mood variability.

**Model Formula**: `log_mood_std ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect + (1 | participant_id)`

**Parameters**:
- `df` (pd.DataFrame): Preprocessed daily aggregates with log-transformed outcome.

**Returns**:
- `object`: Fitted LMM model object (from `statsmodels`).

---

### `fit_lmm_mean(df: pd.DataFrame) -> object`

Fits the secondary Linear Mixed-Effects Model for mean mood.

**Model Formula**: `mean_mood ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect + (1 | participant_id)`

**Parameters**:
- `df` (pd.DataFrame): Preprocessed daily aggregates.

**Returns**:
- `object`: Fitted LMM model object.

---

### `extract_model_coefficients(model: object) -> dict`

Extracts fixed-effect coefficients, standard errors, p-values, and 95% CIs from a fitted LMM.

**Parameters**:
- `model` (object): Fitted LMM model.

**Returns**:
- `dict`: Dictionary with keys `fixed_effects` and `random_effects`.

---

### `run_model_diagnostics(model: object, df: pd.DataFrame) -> dict`

Performs model diagnostics including Shapiro-Wilk test and Breusch-Pagan test, and generates residual plots.

**Parameters**:
- `model` (object): Fitted LMM model.
- `df` (pd.DataFrame): Data used for fitting.

**Returns**:
- `dict`: Dictionary containing diagnostic test results and plot file paths.

---

### `run_lopo_cv(df: pd.DataFrame, model_fn: callable) -> dict`

Performs Leave-One-Participant-Out cross-validation.

**Parameters**:
- `df` (pd.DataFrame): Full dataset.
- `model_fn` (callable): Function to fit the model.

**Returns**:
- `dict`: Contains `average_rmse` and `sign_consistency_pct`.

---

### `run_sensitivity_weekdays(df: pd.DataFrame, model_fn: callable) -> dict`

Runs sensitivity analysis on weekdays-only data.

**Parameters**:
- `df` (pd.DataFrame): Full dataset.
- `model_fn` (callable): Function to fit the model.

**Returns**:
- `dict`: Contains `total_steps` coefficient, p-value, and consistency flags.

---

### `run_sensitivity_active_minutes(df: pd.DataFrame, model_fn: callable) -> dict`

Runs sensitivity analysis using "active minutes" instead of step counts.

**Parameters**:
- `df` (pd.DataFrame): Full dataset.
- `model_fn` (callable): Function to fit the model.

**Returns**:
- `dict`: Contains comparison results.

---

### `run_sensitivity_single_rating_bootstrap(df: pd.DataFrame, n_iterations: int) -> dict`

Runs bootstrap sensitivity analysis for single-rating handling.

**Parameters**:
- `df` (pd.DataFrame): Full dataset.
- `n_iterations` (int): Number of bootstrap iterations (from `config.BOOTSTRAP_ITERATIONS`).

**Returns**:
- `dict`: Contains `consistency_pct` and `pass` flag (True if >= 80%).

---

### `append_lopo_and_sensitivity_results(base_results: dict, lopo_results: dict, sensitivity_results: dict) -> dict`

Merges base model results with LOPO and sensitivity analysis outputs.

**Parameters**:
- `base_results` (dict): Base model results from `extract_model_coefficients`.
- `lopo_results` (dict): Results from `run_lopo_cv`.
- `sensitivity_results` (dict): Combined sensitivity analysis results.

**Returns**:
- `dict`: Complete results dictionary conforming to `model_results.schema.yaml`.

---

### `validate_against_schema(data: dict, schema_path: str) -> bool`

Validates a dictionary against a YAML schema.

**Parameters**:
- `data` (dict): Data to validate.
- `schema_path` (str): Path to the schema file.

**Returns**:
- `bool`: True if valid, False otherwise.

---

### `run_analysis() -> dict`

Orchestrates the full analysis pipeline: loading data, fitting models, running diagnostics, LOPO, and sensitivity analyses.

**Returns**:
- `dict`: Complete model results dictionary.

---

### `main()`

Entry point for the analysis script. Executes `run_analysis()` and saves results to `data/processed/model_results.json`.
