# API Reference

This document provides detailed API documentation for all modules in the Feature Importance Drift Analysis Pipeline.

## Module: `code/download.py`

### Functions

#### `calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str`

Calculate the hash of a file.

**Parameters:**
- `file_path`: Path to the file
- `algorithm`: Hash algorithm to use (default: "sha256")

**Returns:** Hex digest of the file hash

**Example:**
```python
from pathlib import Path
from download import calculate_file_hash

hash_value = calculate_file_hash(Path("data/raw/dataset.zip"))
```

#### `download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool`

Download a file from a URL.

**Parameters:**
- `url`: Source URL
- `dest_path`: Destination path
- `chunk_size`: Size of chunks for downloading (default: 8192)

**Returns:** True if download successful, False otherwise

#### `verify_dataset(file_path: Path, expected_hash: Optional[str] = None) -> Tuple[bool, str]`

Verify the downloaded dataset.

**Parameters:**
- `file_path`: Path to the downloaded file
- `expected_hash`: Expected hash value (optional)

**Returns:** Tuple of (is_valid, message)

#### `main() -> None`

Main entry point for the download module.

---

## Module: `code/preprocess.py`

### Functions

#### `load_raw_dataset(file_path: Path) -> pd.DataFrame`

Load and parse the raw dataset.

**Parameters:**
- `file_path`: Path to the dataset file

**Returns:** Pandas DataFrame with the dataset

#### `handle_missing_values(df: pd.DataFrame) -> pd.DataFrame`

Handle missing values via median imputation.

**Parameters:**
- `df`: Input DataFrame

**Returns:** DataFrame with missing values filled

#### `check_variance(df: pd.DataFrame, threshold: float = 0.0) -> Tuple[pd.DataFrame, List[str]]`

Check feature variance and drop zero-variance features.

**Parameters:**
- `df`: Input DataFrame
- `threshold`: Variance threshold (default: 0.0)

**Returns:** Tuple of (filtered DataFrame, list of dropped feature names)

#### `split_into_windows(df: pd.DataFrame, window_size_days: int = 30) -> List[pd.DataFrame]`

Split data into sequential time windows.

**Parameters:**
- `df`: Input DataFrame (must have datetime index)
- `window_size_days`: Size of each window in days (default: 30)

**Returns:** List of DataFrames, one per window

#### `process_and_save_windows(df: pd.DataFrame, output_dir: Path) -> List[Path]`

Process and save individual windows to disk.

**Parameters:**
- `df`: Input DataFrame
- `output_dir`: Directory to save processed windows

**Returns:** List of paths to saved window files

#### `main() -> None`

Main entry point for the preprocess module.

---

## Module: `code/train_and_importance.py`

### Functions

#### `load_window_data(window_path: Path) -> Tuple[np.ndarray, np.ndarray]`

Load features and target from a window file.

**Parameters:**
- `window_path`: Path to the window file

**Returns:** Tuple of (features array, target array)

#### `prepare_features_target(df: pd.DataFrame, target_column: str = "ML1_sum") -> Tuple[np.ndarray, np.ndarray]`

Prepare features and target from a DataFrame.

**Parameters:**
- `df`: Input DataFrame
- `target_column`: Name of target column (default: "ML1_sum")

**Returns:** Tuple of (features array, target array)

#### `train_model(X: np.ndarray, y: np.ndarray, params: Dict[str, Any] = None) -> RandomForestRegressor`

Train a Random Forest Regressor.

**Parameters:**
- `X`: Feature matrix
- `y`: Target vector
- `params`: Model parameters (default: n_estimators=100, max_depth=10, random_state=42)

**Returns:** Trained RandomForestRegressor

#### `evaluate_model(model, X: np.ndarray, y: np.ndarray) -> float`

Evaluate model performance using R² score.

**Parameters:**
- `model`: Trained model
- `X`: Feature matrix
- `y`: Target vector

**Returns:** R² score

#### `validate_model_performance(r_squared: float, threshold: float = 0.8) -> bool`

Check if model performance meets threshold.

**Parameters:**
- `r_squared`: Model R² score
- `threshold`: Minimum acceptable R² (default: 0.8)

**Returns:** True if performance meets threshold

#### `calculate_importance(model, X: np.ndarray, y: np.ndarray, n_repeats: int = 10) -> Dict[str, float]`

Calculate permutation feature importance.

**Parameters:**
- `model`: Trained model
- `X`: Feature matrix
- `y`: Target vector
- `n_repeats`: Number of repeats for permutation (default: 10)

**Returns:** Dictionary mapping feature names to importance scores

#### `save_importance_profile(profile: Dict[str, Any], output_path: Path) -> None`

Save importance profile to CSV.

**Parameters:**
- `profile`: Importance profile dictionary
- `output_path`: Path to save the CSV file

#### `main() -> None`

Main entry point for the train_and_importance module.

---

## Module: `code/drift_analysis.py`

### Functions

#### `load_importance_profiles(profiles_path: Path) -> pd.DataFrame`

Load importance profiles from CSV.

**Parameters:**
- `profiles_path`: Path to importance_profiles.csv

**Returns:** DataFrame with importance profiles

#### `extract_window_rankings(profiles: pd.DataFrame, window_id: str) -> Dict[str, float]`

Extract feature rankings for a specific window.

**Parameters:**
- `profiles`: Importance profiles DataFrame
- `window_id`: Window identifier

**Returns:** Dictionary mapping feature names to ranks

#### `calculate_rank_correlation(rankings_t: Dict[str, float], rankings_t1: Dict[str, float]) -> Tuple[float, float]`

Calculate Spearman rank correlation between two windows.

**Parameters:**
- `rankings_t`: Rankings from window T
- `rankings_t1`: Rankings from window T+1

**Returns:** Tuple of (Spearman rho, p-value)

#### `compute_pairwise_drift(profiles: pd.DataFrame) -> List[Dict[str, Any]]`

Compute pairwise drift metrics for all consecutive windows.

**Parameters:**
- `profiles`: Importance profiles DataFrame

**Returns:** List of drift metric dictionaries

#### `load_null_baseline(baseline_path: Path) -> Dict[str, Any]`

Load null baseline from JSON file.

**Parameters:**
- `baseline_path`: Path to null_baseline.json

**Returns:** Null baseline dictionary

#### `flag_high_drift(drift_metrics: List[Dict], p_values: List[float], threshold: float = 0.05) -> List[Dict]`

Flag transitions with significant drift.

**Parameters:**
- `drift_metrics`: List of drift metric dictionaries
- `p_values`: List of p-values from significance test
- `threshold`: Significance threshold (default: 0.05)

**Returns:** Filtered list of high drift events

#### `main() -> None`

Main entry point for the drift_analysis module.

---

## Module: `code/significance_test.py`

### Functions

#### `load_correlation_sequence(metrics_path: Path) -> List[float]`

Load correlation sequence from drift metrics.

**Parameters:**
- `metrics_path`: Path to drift_metrics.csv

**Returns:** List of Spearman rho values

#### `mann_kendall_test(sequence: List[float]) -> Tuple[float, float]`

Perform Mann-Kendall trend test.

**Parameters:**
- `sequence`: List of correlation values

**Returns:** Tuple of (Kendall's Tau, p-value)

#### `block_permutation_test(sequence: List[float], n_resamples: int = 1000, block_size: int = 5) -> float`

Perform block permutation significance test.

**Parameters:**
- `sequence`: List of correlation values
- `n_resamples`: Number of resamples (default: 1000)
- `block_size`: Block size for permutation (default: 5)

**Returns:** Permutation p-value

#### `run_significance_tests(metrics_path: Path) -> Dict[str, Any]`

Run all significance tests on the correlation sequence.

**Parameters:**
- `metrics_path`: Path to drift_metrics.csv

**Returns:** Dictionary with test results

#### `main() -> None`

Main entry point for the significance_test module.

---

## Module: `code/generate_final_report.py`

### Functions

#### `load_drift_metrics(metrics_path: Path) -> pd.DataFrame`

Load drift metrics from CSV.

**Parameters:**
- `metrics_path`: Path to drift_metrics.csv

**Returns:** DataFrame with drift metrics

#### `load_stability_report(report_path: Path) -> Dict[str, Any]`

Load stability report from JSON.

**Parameters:**
- `report_path`: Path to stability_report.json

**Returns:** Stability metrics dictionary

#### `aggregate_global_stats(drift_metrics: pd.DataFrame, stability_report: Dict) -> Dict[str, Any]`

Aggregate all metrics into global statistics.

**Parameters:**
- `drift_metrics`: DataFrame with drift metrics
- `stability_report`: Stability metrics dictionary

**Returns:** Dictionary with aggregated global statistics

#### `save_final_report(stats: Dict[str, Any], output_path: Path) -> None`

Save final report to JSON.

**Parameters:**
- `stats`: Global statistics dictionary
- `output_path`: Path to save the JSON file

#### `main() -> None`

Main entry point for the generate_final_report module.

---

## Module: `code/utils/config.py`

### Classes

#### `Config`

Configuration container dataclass.

**Attributes:**
- `data_dir`: Path to data directory
- `output_dir`: Path to output directory
- `log_level`: Logging level
- `window_size_days`: Window size in days
- `model_params`: Model parameters dictionary
- `min_r_squared`: Minimum R² threshold
- `n_permutation_resamples`: Number of permutation resamples
- `block_size`: Block size for permutation test

### Functions

#### `get_config() -> Config`

Get the singleton configuration instance.

#### `reset_config() -> None`

Reset the configuration to defaults.

#### `load_config_from_env() -> Config`

Load configuration from environment variables.

---

## Module: `code/utils/logger.py`

### Functions

#### `setup_logger(name: str, log_file: Optional[Path] = None, level: Optional[str] = None) -> logging.Logger`

Set up a logger with console and optional file handler.

#### `get_logger(name: str) -> logging.Logger`

Get a logger instance (creates if doesn't exist).

---

## Module: `code/utils/stats_aggregator.py`

### Functions

#### `calculate_stability_metrics(r_squared_values: List[float], successful_windows: int, total_windows: int) -> Dict[str, Any]`

Calculate stability metrics from model performance.

#### `aggregate_from_profiles(profiles_path: Path) -> Dict[str, Any]`

Aggregate stability metrics from importance profile CSV.

#### `save_stability_report(metrics: Dict[str, Any], output_path: Path) -> None`

Save stability metrics report to JSON file.
