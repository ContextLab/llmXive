# API Reference

This document provides a comprehensive reference for the `code/` module APIs used in the Equivalence Principle testing pipeline.

## `code/config.py`

### Classes

#### `Config`
Dataclass holding all configuration parameters loaded from `config.yaml`.

**Attributes:**
- `paths` (Dict): Path configuration for data directories
- `benchmark_values` (Dict): Benchmark values including `etvos_limit`
- `hyperparams` (Dict): Hyperparameters for the pipeline

#### `get_config()`
```python
def get_config(config_path: str = "config.yaml") -> Config
```
Loads and returns the configuration object. Raises `FileNotFoundError` if `benchmark_values.etvos_limit` is missing.

**Returns:** `Config` object

**Raises:**
- `FileNotFoundError`: If benchmark value is missing
- `yaml.YAMLError`: If config file is malformed

---

## `code/utils/logging.py`

### Exceptions

- `PipelineError`: Base exception for pipeline errors
- `DataUnavailableError`: Raised when required data is missing
- `ConfigurationError`: Raised for configuration issues
- `AnalysisError`: Raised for analysis failures
- `ModelConvergenceError`: Raised when solver fails to converge
- `ValidationError`: Raised for validation failures
- `ModelError`: Raised for model definition issues

### Functions

#### `init_logging()`
Configures logging to both file and console handlers.

#### `get_logger(name: str) -> logging.Logger`
Returns a logger instance with the given name.

#### `log_progress(step: str, message: str)`
Logs a progress message with timestamp.

#### `log_error(message: str)`
Logs an error message with traceback if available.

#### `handle_fatal_error(error: Exception)`
Handles fatal errors by logging and exiting.

#### `log_step_duration(step: TimedStep)`
Logs the duration of a timed step.

---

## `code/models/entities.py`

### Dataclasses

#### `NormalPoint`
Represents a single SLR normal point observation.

**Fields:**
- `timestamp` (datetime): Observation time
- `range` (float): Range in meters
- `satellite_id` (str): Satellite identifier
- `station_id` (str): Station identifier
- `quality_flag` (str): Quality indicator

#### `OrbitSolution`
Represents a fitted orbit solution.

**Fields:**
- `orbital_elements` (Dict): Orbital elements (semi_major_axis_m, eccentricity, inclination_rad, raan_rad, arg_perigee_rad, mean_anomaly_rad)
- `non_gravitational_acceleration` (float): m/s²
- `covariance_matrix` (np.ndarray): N x N covariance matrix
- `chi2` (float): Chi-squared statistic
- `residuals` (np.ndarray): M residuals
- `state` (np.ndarray): Position vector (3,) in meters at reference epoch

#### `EotvosResult`
Represents the final Eötvös parameter result.

**Fields:**
- `eta_value` (float): Eötvös parameter
- `confidence_interval` (Tuple[float, float]): 95% CI bounds
- `p_value` (float): Statistical p-value
- `sensitivity_sweep_data` (Dict[str, float]): Model name -> z_score mapping

---

## `code/data/ingestion.py`

### Exceptions

- `DataIngestionError`: Base exception for data ingestion failures

### Functions

#### `validate_config(config: Config)`
Validates the configuration object.

#### `fetch_satellite_data(satellite_id: str, url: str) -> bytes`
Fetches raw SLR data for a satellite with retry logic.

**Returns:** Raw bytes of the SLR file

#### `parse_slr_file(raw_content: bytes) -> List[NormalPoint]`
Parses raw SLR file content into a list of `NormalPoint` objects.

**Returns:** List of `NormalPoint` objects

#### `aggregate_satellites(satellite_ids: List[str]) -> pd.DataFrame`
Fetches and aggregates data for multiple satellites.

**Returns:** Pandas DataFrame with all observations

#### `verify_data_availability_wrapper()`
Wrapper to verify data availability and generate feasibility gap reports.

---

## `code/data/preprocessing.py`

### Functions

#### `filter_residuals(df: pd.DataFrame, threshold_cm: float = 2.0) -> pd.DataFrame`
Filters out observations with residuals exceeding the threshold.

**Returns:** Filtered DataFrame

#### `handle_sparse_satellites(df: pd.DataFrame, min_days: int = 30) -> Tuple[pd.DataFrame, List[str]]`
Identifies and excludes satellites with insufficient arc length.

**Returns:** Tuple of (filtered DataFrame, list of excluded satellite IDs)

#### `align_time_series(df: pd.DataFrame) -> pd.DataFrame`
Aligns time series across multiple satellites.

#### `merge_multi_satellite_datasets(dfs: List[pd.DataFrame]) -> pd.DataFrame`
Merges multiple satellite datasets into a single DataFrame.

#### `preprocess_slr_data(df: pd.DataFrame) -> pd.DataFrame`
Full preprocessing pipeline: filtering, sparse handling, alignment.

#### `main()`
Entry point for preprocessing script.

---

## `code/data/output.py`

### Functions

#### `compute_sha256(file_path: str) -> str`
Computes SHA-256 hash of a file.

#### `save_cleaned_data(df: pd.DataFrame, output_path: str)`
Saves cleaned data to CSV with checksum verification.

#### `record_checksum(file_path: str, state_path: str)`
Records file checksum in the project state file.

#### `save_orbit_solution(solution: OrbitSolution, output_path: str)`
Saves orbit solution to JSON.

#### `save_eotvos_metrics(result: EotvosResult, output_path: str)`
Saves Eötvös metrics to JSON.

#### `run_output_pipeline()`
Orchestrates the full output pipeline.

---

## `code/models/dynamics.py`

### Functions

#### `compute_geopotential_acceleration(state: np.ndarray, time: Time, model: str = "GGM05C") -> np.ndarray`
Computes geopotential acceleration using specified model.

**Returns:** Acceleration vector (3,) in m/s²

#### `compute_jacchia_drag_acceleration(state: np.ndarray, time: Time, satellite_params: Dict) -> np.ndarray`
Computes Jacchia drag acceleration.

**Returns:** Acceleration vector (3,) in m/s²

#### `compute_srp_acceleration(state: np.ndarray, time: Time, satellite_params: Dict) -> np.ndarray`
Computes Solar Radiation Pressure acceleration.

**Returns:** Acceleration vector (3,) in m/s²

#### `compute_relativistic_acceleration(state: np.ndarray, time: Time) -> np.ndarray`
Computes relativistic corrections (Schwarzschild, Lense-Thirring).

**Returns:** Acceleration vector (3,) in m/s²

#### `DynamicsModel`
Class encapsulating all force models.

#### `compute_acceleration(state: np.ndarray, time: Time, satellite_params: Dict) -> np.ndarray`
Computes total acceleration from all force models.

---

## `code/models/estimator.py`

### Classes

#### `OrbitSolution`
(See `code/models/entities.py`)

### Functions

#### `stack_residuals(residuals_sat1: List[np.array], residuals_sat2: List[np.array]) -> np.array`
Stacks residuals from two satellites for joint fitting.

#### `separate_fit_satellite(satellite_data: pd.DataFrame, model_params: Dict) -> OrbitSolution`
Performs separate least-squares fit for a single satellite.

**Returns:** `OrbitSolution` object

#### `run_joint_fit(data_sat1: pd.DataFrame, data_sat2: pd.DataFrame, model_params: Dict) -> OrbitSolution`
Performs joint least-squares fit for two satellites.

**Returns:** `OrbitSolution` object

#### `extract_joint_parameters(solution: OrbitSolution) -> Dict`
Extracts differential acceleration and covariance from joint solution.

**Returns:** Dictionary with `ac`, `g`, `covariance`

---

## `code/analysis/eotvos.py`

### Classes

#### `EotvosResult`
(See `code/models/entities.py`)

### Functions

#### `compute_eotvos_parameter(ac: float, g: float, covariance: np.ndarray) -> EotvosResult`
Computes Eötvös parameter and confidence interval.

**Returns:** `EotvosResult` object

#### `run_eotvos_analysis(separate_solutions: List[OrbitSolution], joint_solution: OrbitSolution) -> EotvosResult`
Full Eötvös analysis pipeline.

**Returns:** `EotvosResult` object

#### `main()`
Entry point for Eötvös analysis script.

---

## `code/analysis/validation.py`

### Classes

#### `ModelComparisonResult`
**Fields:** `chi2_null`, `chi2_alt`, `F_statistic`, `p_value`, `BIC`

#### `SensitivityReport`
**Fields:** `results_per_model`, `z_score_variation`, `final_flag`

### Functions

#### `compute_ssr(residuals: np.ndarray) -> float`
Computes sum of squared residuals.

#### `compute_bic(chi2: float, dof: int, n: int) -> float`
Computes Bayesian Information Criterion.

#### `perform_f_test(chi2_null: float, chi2_alt: float, dof_null: int, dof_alt: int) -> Dict`
Performs F-test and returns F-statistic and p-value.

#### `compare_null_vs_alternative(null_solution: OrbitSolution, alt_solution: OrbitSolution) -> ModelComparisonResult`
Compares null vs alternative model.

**Returns:** `ModelComparisonResult` object

#### `iterate_geopotential_models(models: List[str]) -> Iterator[str]`
Iterates over geopotential models for sensitivity analysis.

#### `run_sensitivity_per_model(model: str, data: pd.DataFrame) -> EotvosResult`
Runs estimator for a specific geopotential model.

#### `aggregate_sensitivity_results(results: List[EotvosResult]) -> SensitivityReport`
Aggregates sensitivity results.

#### `apply_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]`
Applies multiple comparison correction (Bonferroni, Holm-Bonferroni, Benjamini-Hochberg).

#### `run_sensitivity_analysis(data: pd.DataFrame) -> SensitivityReport`
Full sensitivity analysis pipeline.

#### `main()`
Entry point for validation script.

---

## `code/cli/main.py`

### Functions

#### `check_memory_limit(limit_gb: float = 6.0) -> bool`
Checks if current memory usage exceeds the limit.

**Returns:** True if limit exceeded, False otherwise

#### `run_pipeline_with_monitoring()`
Runs the full pipeline with memory and time monitoring.

#### `main()`
CLI entry point with argument parsing.

---

## `code/scripts/`

### `run_ingestion_pipeline.py`
Entry point for data ingestion pipeline.

**Functions:** `main()`

### `validate_quickstart.py`
Entry point for quickstart validation.

**Functions:** `setup_logging()`, `check_config_files()`, `verify_data_artifacts()`, `run_lightweight_pipeline()`, `validate_outputs()`, `main()`
