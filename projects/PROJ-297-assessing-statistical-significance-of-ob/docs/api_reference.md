# API Reference

## Module: `code/config.py`

### Functions

#### `get_config() -> Dict[str, Any]`
Returns the configuration dictionary with paths, seeds, and thresholds.

#### `ensure_dirs() -> None`
Creates all required directories (raw data, processed data, outputs) if they don't exist.

---

## Module: `code/loaders.py`

### Functions

#### `fetch_uci_dataset(dataset_id: str) -> pd.DataFrame`
Fetches a dataset from the UCI repository by ID. Raises `FileNotFoundError` if download fails.

#### `load_dataset_from_path(path: str) -> pd.DataFrame`
Loads a dataset from a local CSV file.

#### `drop_missing_values(df: pd.DataFrame) -> pd.DataFrame`
Removes rows with any missing values.

#### `detect_constant_variables(df: pd.DataFrame) -> List[str]`
Returns a list of column names that have zero variance.

#### `exclude_constant_variables(df: pd.DataFrame) -> pd.DataFrame`
Removes constant variables from the dataframe.

#### `filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame`
Keeps only continuous (numeric) variables.

#### `validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = 20) -> bool`
Validates that the dataset has at least `min_vars` continuous variables.

#### `apply_hygiene_pipeline(df: pd.DataFrame) -> pd.DataFrame`
Applies the full hygiene pipeline: drop missing, exclude constant, filter continuous.

#### `load_and_hygiene_dataset(dataset_id: str) -> pd.DataFrame`
Fetches a dataset and applies the full hygiene pipeline in one step.

---

## Module: `code/stats_engine.py`

### Functions

#### `compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame`
Computes the correlation matrix for a dataframe. Supports 'pearson' and 'spearman'.

#### `construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph`
Constructs a graph from a correlation matrix, keeping edges where |r| > threshold.

#### `calculate_stats(graph: nx.Graph, corr_matrix: pd.DataFrame) -> Dict[str, float]`
Calculates network statistics: mean absolute correlation, edge density, max absolute correlation, average clustering coefficient.

#### `generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: Callable) -> Dict[str, List[float]]`
Generates null distributions by permuting the data and computing statistics for each permutation.

#### `generate_synthetic_dataset(n_samples: int = 500, n_vars: int = 20) -> pd.DataFrame`
Generates a synthetic dataset with identity covariance (no true correlations) for validation.

#### `validate_null_model() -> bool`
Runs the synthetic validation loop (100 times) and verifies p > 0.05 in >=95% of runs.

#### `compute_correlation_matrix_with_stats(df: pd.DataFrame) -> Dict[str, pd.DataFrame]`
Computes both Pearson and Spearman correlation matrices.

#### `calculate_empirical_p_value(observed: float, null_dist: List[float]) -> float`
Calculates the empirical p-value using the (r+1)/(N+1) formula.

#### `save_exploratory_spearman_matrices(results: Dict) -> None`
Saves Spearman matrices to `output/exploratory/` for exploratory comparison.

#### `apply_benjamini_yekutieli_correction(p_values: List[float]) -> List[float]`
Applies the BY correction to a list of p-values.

#### `run_full_analysis_pipeline(dataset_ids: List[str]) -> Dict`
Runs the complete analysis pipeline on a list of datasets.

---

## Module: `code/correction.py`

### Functions

#### `benjamini_yekutieli(p_values: List[float]) -> List[float]`
Implements the Benjamini-Yekutieli procedure for FDR control under arbitrary dependence.

#### `apply_correction_to_results(results: Dict) -> Dict`
Applies BY correction to all p-values in the results dictionary and adds q-values and significance flags.

---

## Module: `code/viz.py`

### Functions

#### `plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None`
Generates a high-resolution heatmap of a correlation matrix.

#### `plot_histogram(null_dist: List[float], observed_val: float, title: str, output_path: str) -> None`
Generates a histogram of a null distribution with the observed value overlaid.

#### `plot_primary_threshold_visualizations(dataset_id: str, results: Dict, threshold: float = 0.3) -> None`
Generates heatmap and histogram for the primary threshold (|r| > 0.3).

#### `plot_sensitivity_sweep(sweep_results: Dict) -> None`
Generates visualizations for the threshold sensitivity sweep.

#### `plot_observed_vs_null_heatmap(observed_matrix: pd.DataFrame, null_mean_matrix: pd.DataFrame, output_path: str) -> None`
Compares observed correlation matrix with the mean of the null distribution.

---

## Module: `code/main.py`

### Functions

#### `integrate_visualizations(results: Dict) -> None`
Integrates visualization generation into the pipeline results.

#### `generate_sensitivity_report(results: Dict, thresholds: List[float]) -> pd.DataFrame`
Generates a sensitivity report table showing significant counts per threshold.

#### `main() -> None`
Entry point for the pipeline. Orchestrates data loading, analysis, correction, and reporting.
