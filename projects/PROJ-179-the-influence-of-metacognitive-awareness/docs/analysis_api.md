# API Documentation: Analysis Modules

This document provides the API reference for the analysis modules within the `code/src/analysis/` directory.
These modules implement the statistical pipelines for User Stories 1, 2, and 3.

## `code/src/analysis/correlation.py`

Implements the primary correlation analysis (US1) using a Hold-Out design.

### Classes

- **`TolerantConfig`**: A configuration wrapper that allows dictionary-style access (`.get()`) to nested configuration values without raising `KeyError`.

### Functions

- **`load_trial_data(filepath: str) -> pd.DataFrame`**
 Loads the preprocessed trial data from a CSV file.
 - *Returns*: DataFrame containing `participant_id`, `trial_id`, `stimulus_modality`, `source_label`, `participant_response`, `confidence_rating`.

- **`compute_hold_out_metrics(df: pd.DataFrame, train_ratio: float = 0.7, seed: int = 42) -> Dict[str, Any]`**
 Computes metacognitive awareness (Type-2 AUC) on the training split and reality testing accuracy (d') on the held-out test split.
 - *Parameters*:
 - `df`: Input trial data.
 - `train_ratio`: Proportion of trials for training (default 0.7).
 - `seed`: Random seed for reproducibility.
 - *Returns*: Dictionary with `meta_auc`, `d_prime`, `train_indices`, `test_indices`.

- **`write_results(results: Dict[str, Any], output_path: str) -> None`**
 Serializes the correlation results to a JSON file.

- **`main() -> int`**
 Entry point for the script. Orchestrates loading, computing, and writing results.

---

## `code/src/analysis/bootstrap.py`

Implements bootstrap resampling for confidence interval estimation.

### Functions

- **`load_correlation_data(filepath: str) -> Tuple[np.ndarray, np.ndarray]`**
 Loads the paired metacognitive scores and accuracy scores.
 - *Returns*: Tuple of (meta_auc_array, d_prime_array).

- **`compute_correlation_statistic(x: np.ndarray, y: np.ndarray) -> float`**
 Computes the Pearson correlation coefficient.

- **`run_bootstrap_analysis(x: np.ndarray, y: np.ndarray, n_resamples: int = 1000, seed: int = 42) -> Dict[str, Any]`**
 Runs the bootstrap resampling loop.
 - *Returns*: Dictionary containing `r_value`, `p_value`, `ci_95_lower`, `ci_95_upper`, `bootstrap_count`.

- **`write_results(results: Dict[str, Any], output_path: str) -> None`**
 Writes the bootstrap configuration and results to `data/results/bootstrap_config.json`.

- **`main() -> int`**
 Entry point for the script.

---

## `code/src/analysis/regression.py`

Implements hierarchical regression analysis with covariates (US2).

### Functions

- **`load_regression_data(filepath: str) -> pd.DataFrame`**
 Loads data required for regression, including metacognitive scores, accuracy, and covariates (age, gender, working_memory if available).

- **`compute_type2_auc(confidence: np.ndarray, accuracy: np.ndarray) -> float`**
 Computes Type-2 AUC (meta-d') for a given set of trials.

- **`compute_d_prime(hit_rate: float, false_alarm_rate: float) -> float`**
 Computes d' (sensitivity) from hit and false alarm rates.

- **`run_regression_analysis(df: pd.DataFrame) -> Dict[str, Any]`**
 Executes the hierarchical regression:
 1. Model 1: Covariates (Age, Gender, [Working Memory]).
 2. Model 2: Covariates + Metacognitive Score.
 - *Returns*: Dictionary with `model_1_r2`, `model_2_r2`, `delta_r2`, `f_change`, `p_change`, `coefficients`.

- **`main() -> int`**
 Entry point for the script. Writes results to `data/results/regression_analysis.json`.

---

## `code/src/analysis/diagnostics.py`

Performs statistical assumption checks for regression models.

### Functions

- **`load_regression_results(filepath: str) -> Dict[str, Any]`**
 Loads the regression analysis results.

- **`check_normality_of_residuals(residuals: np.ndarray) -> Dict[str, Any]`**
 Performs Shapiro-Wilk test on residuals.
 - *Returns*: `{'statistic': float, 'p_value': float, 'is_normal': bool}`.

- **`check_homoscedasticity(residuals: np.ndarray, predicted: np.ndarray) -> Dict[str, Any]`**
 Performs Breusch-Pagan test for heteroscedasticity.
 - *Returns*: `{'statistic': float, 'p_value': float, 'is_homoscedastic': bool}`.

- **`calculate_vif(df: pd.DataFrame, target_col: str) -> Dict[str, float]`**
 Calculates Variance Inflation Factor for each predictor.
 - *Returns*: Dictionary mapping feature names to VIF scores.

- **`run_diagnostics(df: pd.DataFrame, results: Dict[str, Any]) -> Dict[str, Any]`**
 Orchestrates all diagnostic checks.

- **`main() -> int`**
 Entry point for the script.

---

## `code/src/analysis/filter.py`

Splits data by stimulus modality for robustness analysis (US3).

### Functions

- **`setup_directories() -> None`**
 Ensures output directories exist.

- **`load_trial_data(filepath: str) -> pd.DataFrame`**
 Loads the full trial dataset.

- **`filter_by_modality(df: pd.DataFrame, modality: str) -> pd.DataFrame`**
 Filters the dataframe by `stimulus_modality`.

- **`write_output(df: pd.DataFrame, filepath: str) -> None`**
 Writes the filtered dataframe to CSV.

- **`run_filter_analysis() -> None`**
 Executes the filtering pipeline, producing `data/derived/visual_trials.csv` and `data/derived/auditory_trials.csv`.

- **`main() -> int`**
 Entry point for the script.

---

## `code/src/analysis/robustness.py`

Runs correlation analysis on modality-specific subsets (US3).

### Functions

- **`load_filtered_data(modality: str) -> pd.DataFrame`**
 Loads the pre-filtered data for a specific modality.

- **`compute_hold_out_metrics_for_modality(df: pd.DataFrame, modality: str) -> Dict[str, Any]`**
 Runs the hold-out metrics computation specifically for a modality subset.

- **`run_bootstrap_correlation(df: pd.DataFrame, n_resamples: int = 1000) -> Dict[str, Any]`**
 Runs bootstrap correlation on the subset.

- **`write_results(modality: str, results: Dict[str, Any], output_dir: str) -> None`**
 Writes results for a specific modality.

- **`run_robustness_analysis() -> None`**
 Orchestrates the analysis for both visual and auditory modalities.

- **`main() -> int`**
 Entry point for the script. Writes `data/results/robustness_analysis.json`.

---

## `code/src/report/generate.py`

Generates final JSON reports for all analysis stages.

### Functions

- **`load_bootstrap_results(filepath: str) -> Dict[str, Any]`**
 Loads bootstrap results.

- **`load_regression_results(filepath: str) -> Dict[str, Any]`**
 Loads regression results.

- **`determine_correlation_direction(r: float) -> str`**
 Returns 'positive', 'negative', or 'none'.

- **`calculate_effect_size_magnitude(r: float) -> str`**
 Returns effect size label (e.g., 'small', 'medium', 'large').

- **`apply_bonferroni_correction(p_values: List[float], family_size: int) -> List[float]`**
 Applies Bonferroni correction.

- **`apply_bh_correction(p_values: List[float]) -> List[float]`**
 Applies Benjamini-Hochberg correction.

- **`generate_primary_analysis_report(results: Dict[str, Any]) -> Dict[str, Any]`**
 Formats the primary analysis output.

- **`write_report(data: Dict[str, Any], filepath: str) -> None`**
 Writes the final report to JSON.

- **`main() -> int`**
 Entry point for the script. Generates `data/results/primary_analysis.json`, `data/results/regression_analysis.json`, and `data/results/robustness_analysis.json`.
