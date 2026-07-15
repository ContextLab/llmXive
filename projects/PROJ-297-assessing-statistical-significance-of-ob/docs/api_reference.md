# API Reference

## Overview

This document provides detailed API documentation for the statistical significance assessment pipeline.

## Module: `code/config.py`

### Functions

#### `get_config()`

Returns the configuration dictionary containing all project settings.

**Returns:**
- `Dict[str, Any]`: Configuration dictionary with keys:
 - `paths`: Dictionary of directory paths
 - `random_seed`: Integer seed for reproducibility
 - `threshold`: Default correlation threshold
 - `n_permutations`: Number of permutations
 - `dataset_requirements`: Minimum dataset requirements

#### `ensure_dirs()`

Creates all required directories if they don't exist.

**Returns:**
- `None`: Creates directories in place

**Raises:**
- `ValueError`: If path configuration is invalid

---

## Module: `code/loaders.py`

### Functions

#### `fetch_uci_dataset(dataset_id: str) -> pd.DataFrame`

Fetches a dataset from the UCI Machine Learning Repository.

**Parameters:**
- `dataset_id`: UCI dataset identifier or URL

**Returns:**
- `pd.DataFrame`: Loaded dataset

**Raises:**
- `FileNotFoundError`: If dataset cannot be found
- `ValueError`: If download fails (no silent fallback)

#### `load_dataset_from_path(path: str) -> pd.DataFrame`

Loads a dataset from a local CSV file.

**Parameters:**
- `path`: Path to CSV file

**Returns:**
- `pd.DataFrame`: Loaded dataset

#### `drop_missing_values(df: pd.DataFrame) -> pd.DataFrame`

Removes rows with any missing values.

**Parameters:**
- `df`: Input DataFrame

**Returns:**
- `pd.DataFrame`: Cleaned DataFrame

#### `detect_constant_variables(df: pd.DataFrame) -> List[str]`

Identifies constant (zero-variance) variables.

**Parameters:**
- `df`: Input DataFrame

**Returns:**
- `List[str]`: List of constant variable names

#### `exclude_constant_variables(df: pd.DataFrame) -> pd.DataFrame`

Removes constant variables from the dataset.

**Parameters:**
- `df`: Input DataFrame

**Returns:**
- `pd.DataFrame`: DataFrame without constant variables

#### `filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame`

Keeps only continuous (numeric) variables.

**Parameters:**
- `df`: Input DataFrame

**Returns:**
- `pd.DataFrame`: DataFrame with only continuous variables

#### `validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = 20) -> bool`

Validates that dataset has sufficient continuous variables.

**Parameters:**
- `df`: Input DataFrame
- `min_vars`: Minimum required variables (default: 20)

**Returns:**
- `bool`: True if validation passes

#### `apply_hygiene_pipeline(df: pd.DataFrame) -> pd.DataFrame`

Applies full data hygiene pipeline.

**Parameters:**
- `df`: Input DataFrame

**Returns:**
- `pd.DataFrame`: Fully cleaned DataFrame

#### `load_and_hygiene_dataset(dataset_id: str) -> pd.DataFrame`

Fetches and applies hygiene pipeline to a dataset.

**Parameters:**
- `dataset_id`: UCI dataset identifier

**Returns:**
- `pd.DataFrame`: Cleaned dataset

---

## Module: `code/stats_engine.py`

### Functions

#### `compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame`

Computes correlation matrix for the dataset.

**Parameters:**
- `df`: Input DataFrame
- `method`: Correlation method ('pearson' or 'spearman')

**Returns:**
- `pd.DataFrame`: Correlation matrix

#### `construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph`

Constructs a graph from correlation matrix above threshold.

**Parameters:**
- `corr_matrix`: Correlation matrix
- `threshold`: Absolute correlation threshold

**Returns:**
- `nx.Graph`: Networkx graph object

#### `calculate_stats(graph: nx.Graph) -> Dict[str, float]`

Calculates network statistics.

**Parameters:**
- `graph`: Networkx graph

**Returns:**
- `Dict[str, float]`: Dictionary of statistics:
 - `mean_abs_corr`: Mean absolute correlation
 - `edge_density`: Edge density
 - `max_abs_corr`: Maximum absolute correlation
 - `avg_clustering`: Average clustering coefficient

#### `generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: Callable) -> Dict[str, Any]`

Generates null distribution via permutation testing.

**Parameters:**
- `df`: Input DataFrame
- `n_permutations`: Number of permutations
- `stats_func`: Function to compute statistic

**Returns:**
- `Dict[str, Any]`: Null distribution results

#### `generate_synthetic_dataset(n_samples: int = 500, n_vars: int = 20) -> pd.DataFrame`

Generates synthetic dataset with identity covariance.

**Parameters:**
- `n_samples`: Number of samples
- `n_vars`: Number of variables

**Returns:**
- `pd.DataFrame`: Synthetic dataset

#### `validate_null_model(n_runs: int = 100) -> Dict[str, Any]`

Validates null model using synthetic data.

**Parameters:**
- `n_runs`: Number of validation runs

**Returns:**
- `Dict[str, Any]`: Validation results including pass rate

#### `compute_correlation_matrix_with_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]`

Computes both Pearson and Spearman correlation matrices.

**Parameters:**
- `df`: Input DataFrame

**Returns:**
- `Dict[str, pd.DataFrame]`: Dictionary with 'pearson' and 'spearman' keys

#### `calculate_empirical_p_value(observed: float, null_dist: List[float]) -> float`

Calculates empirical p-value using (r+1)/(N+1) formula.

**Parameters:**
- `observed`: Observed statistic
- `null_dist`: Null distribution values

**Returns:**
- `float`: Empirical p-value

#### `save_exploratory_spearman_matrices(matrices: Dict[str, pd.DataFrame]) -> None`

Saves Spearman matrices to exploratory directory.

**Parameters:**
- `matrices`: Dictionary of dataset_id to Spearman matrix

**Returns:**
- `None`

#### `apply_benjamini_yekutieli_correction(p_values: List[float]) -> List[float]`

Applies BY correction to p-values.

**Parameters:**
- `p_values`: List of p-values

**Returns:**
- `List[float]`: Corrected q-values

#### `run_full_analysis_pipeline(dataset_ids: List[str], threshold: float, n_permutations: int) -> Dict[str, Any]`

Runs complete analysis pipeline on multiple datasets.

**Parameters:**
- `dataset_ids`: List of dataset identifiers
- `threshold`: Correlation threshold
- `n_permutations`: Number of permutations

**Returns:**
- `Dict[str, Any]`: Complete analysis results

---

## Module: `code/correction.py`

### Functions

#### `benjamini_yekutieli(p_values: List[float]) -> List[float]`

Implements Benjamini-Yekutieli FDR correction.

**Parameters:**
- `p_values`: List of p-values (sorted)

**Returns:**
- `List[float]`: Corrected q-values

#### `apply_correction_to_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]`

Applies BY correction to analysis results.

**Parameters:**
- `results`: List of result dictionaries with p-values

**Returns:**
- `List[Dict[str, Any]]`: Results with q-values and significance flags

---

## Module: `code/viz.py`

### Functions

#### `plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None`

Generates correlation matrix heatmap.

**Parameters:**
- `matrix`: Correlation matrix
- `title`: Plot title
- `output_path`: Output file path (PNG)

**Returns:**
- `None`: Saves plot to file

#### `plot_histogram(null_dist: List[float], observed_val: float, title: str, output_path: str) -> None`

Generates null distribution histogram with observed value.

**Parameters:**
- `null_dist`: Null distribution values
- `observed_val`: Observed statistic
- `title`: Plot title
- `output_path`: Output file path (PNG)

**Returns:**
- `None`: Saves plot to file

#### `plot_primary_threshold_visualizations(results: Dict[str, Any], output_dir: str) -> None`

Generates primary threshold visualizations (|r| > 0.3).

**Parameters:**
- `results`: Analysis results dictionary
- `output_dir`: Output directory

**Returns:**
- `None`: Saves plots to output directory

#### `plot_sensitivity_sweep(sweep_results: Dict[str, Any], output_dir: str) -> None`

Generates sensitivity analysis visualizations.

**Parameters:**
- `sweep_results`: Threshold sweep results
- `output_dir`: Output directory

**Returns:**
- `None`: Saves plots to output directory

#### `plot_observed_vs_null_heatmap(observed: pd.DataFrame, null_mean: pd.DataFrame, output_path: str) -> None`

Generates heatmap comparing observed vs null correlation matrices.

**Parameters:**
- `observed`: Observed correlation matrix
- `null_mean`: Mean null correlation matrix
- `output_path`: Output file path

**Returns:**
- `None`: Saves plot to file

---

## Module: `code/main.py`

### Functions

#### `run_single_validation_run() -> Dict[str, Any]`

Runs a single synthetic validation iteration.

**Returns:**
- `Dict[str, Any]`: Validation results

#### `generate_associational_report(results: Dict[str, Any]) -> None`

Generates associational analysis report.

**Parameters:**
- `results`: Analysis results

**Returns:**
- `None`: Saves report to file

#### `run_threshold_sweep(thresholds: List[float] = [0.1, 0.2, 0.3, 0.4, 0.5]) -> Dict[str, Any]`

Runs threshold sensitivity analysis.

**Parameters:**
- `thresholds`: List of thresholds to test

**Returns:**
- `Dict[str, Any]`: Sensitivity analysis results

#### `generate_sensitivity_report(sweep_results: Dict[str, Any]) -> None`

Generates sensitivity analysis report.

**Parameters:**
- `sweep_results`: Threshold sweep results

**Returns:**
- `None`: Saves report to file

#### `integrate_visualizations(results: Dict[str, Any]) -> None`

Integrates all visualization outputs.

**Parameters:**
- `results`: Complete analysis results

**Returns:**
- `None`: Saves all visualizations

#### `main()`

Main entry point for the pipeline.

**Returns:**
- `None`: Executes full pipeline
