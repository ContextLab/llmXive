# API Reference: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

This document provides function signatures and usage details for the core modules in the `code/` directory.

## `code/utils.py`

Utility functions for seeding, logging, hashing, and timing.

- `set_global_seed(seed: int) -> None`
 - Sets the global random seed for reproducibility across `random`, `numpy`, and `os`.
- `setup_logging(log_level: str = "INFO") -> logging.Logger`
 - Configures the root logger and returns a logger instance.
- `compute_checksum(file_path: str) -> str`
 - Computes the SHA-256 checksum of a file.
- `compute_file_hash(file_path: str) -> str`
 - Alias for `compute_checksum`, returns the hex digest.
- `record_artifact_hash(artifact_path: str, state_file: str) -> None`
 - Records the hash of an artifact into the project state YAML file.
- `get_current_timestamp() -> str`
 - Returns the current timestamp in ISO format.
- `measure_duration(start_time: float) -> float`
 - Returns the elapsed time in seconds since `start_time`.
- `assert_duration_limit(duration: float, limit_seconds: float = 21600) -> None`
 - Raises an error if `duration` exceeds `limit_seconds` (default 6 hours).
- `validate_pipeline_duration(total_duration: float) -> None`
 - Validates the total pipeline duration against the 6-hour limit.
- `start_timer() -> float`
 - Starts a timer and returns the start timestamp.
- `stop_timer(start_time: float) -> float`
 - Stops the timer and returns the duration.

## `code/config.py`

Configuration management and path validation.

- `ensure_directories() -> None`
 - Creates the required directory structure (`data/raw`, `data/processed`, `artifacts`, `state`, `code`, `tests`).
- `validate_paths() -> None`
 - Validates that all required paths exist and are accessible.

## `code/checksums.py`

Functions for data integrity verification.

- `compute_sha256_file(file_path: str) -> str`
 - Computes the SHA-256 hash of a file.
- `scan_raw_data_directory(directory: str) -> List[Dict[str, Any]]`
 - Scans the raw data directory and returns a list of file metadata including checksums.
- `record_checksums_to_state(checksums: List[Dict[str, Any]], state_file: str) -> None`
 - Records the checksums into the project state YAML file.
- `main() -> None`
 - Entry point for the checksum utility script.

## `code/data_loader.py`

Data loading and chunking logic for memory efficiency.

- `DataChunk`
 - Dataclass representing a chunk of data loaded via memory mapping.
 - Fields: `data` (np.ndarray), `metadata` (Dict[str, Any]), `chunk_id` (int).
- `EEGDataLoader`
 - Class for loading EEG data from OpenNeuro or local files.
 - Methods:
 - `__init__(self, dataset_id: str, raw_dir: str)`
 - `load_participant(self, participant_id: str) -> DataChunk`
 - `verify_data_integrity(self) -> bool`
 - `fetch_openneuro_data(self) -> None`
- `main() -> None`
 - Entry point for the data loader script.

## `code/preprocessing.py`

EEG preprocessing and feature extraction.

- `re_reference_to_mastoids(raw: mne.Raw) -> mne.Raw`
 - Re-references the raw EEG data to average mastoids.
- `bandpass_filter_data(raw: mne.Raw, low_freq: float = 1.0, high_freq: float = 40.0) -> mne.Raw`
 - Applies a band-pass filter (1-40 Hz) to the raw data.
- `apply_ica(raw: mne.Raw, n_components: Optional[int] = None) -> mne.ICA`
 - Applies Independent Component Analysis (ICA) for artifact removal.
- `find_and_remove_artifacts(raw: mne.Raw, ica: mne.ICA) -> mne.Raw`
 - Identifies and removes ocular and muscle artifacts using ICA.
- `estimate_valid_duration(raw: mne.Raw) -> float`
 - Estimates the duration of valid EEG data in seconds.
- `extract_microstate_features(raw: mne.Raw, epochs: mne.Epochs) -> Dict[str, Any]`
 - Extracts microstate features (A, B, C, D) and spectral power.
- `preprocess_participant(participant_id: str) -> Dict[str, Any]`
 - Preprocesses data for a single participant and returns features.
- `preprocess_all_participants() -> pd.DataFrame`
 - Preprocesses all participants and returns a feature matrix.
- `main() -> None`
 - Entry point for the preprocessing script.

## `code/modeling.py`

Predictive modeling, cross-validation, and statistical testing.

- `calculate_observed_metric(X: np.ndarray, y: np.ndarray) -> float`
 - Calculates the observed Pearson correlation coefficient.
- `run_bootstrap_ci(X: np.ndarray, y: np.ndarray, n_iterations: int = 200) -> Tuple[float, float]`
 - Performs bootstrap resampling to calculate a 95% confidence interval for Pearson r.
- `calculate_empirical_pvalue(observed_r: float, null_distribution: List[float]) -> float`
 - Calculates the empirical p-value by comparing the observed r to the null distribution.
- `load_null_distribution(path: str) -> List[float]`
 - Loads the null distribution from a file.
- `save_null_distribution(null_distribution: List[float], path: str) -> None`
 - Saves the null distribution to a file.
- `run_modeling_pipeline(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]`
 - Runs the full modeling pipeline including nested CV, permutation test, and bootstrap.
- `main() -> None`
 - Entry point for the modeling script.

## `code/diagnostics.py`

Statistical diagnostics and sensitivity analysis.

- `calculate_vif(X: np.ndarray) -> pd.Series`
 - Calculates Variance Inflation Factors (VIF) for each feature.
- `calculate_permutation_importance(X: np.ndarray, y: np.ndarray) -> pd.Series`
 - Calculates permutation importance scores for all features.
- `apply_benjamini_hochberg(p_values: List[float]) -> List[float]`
 - Applies the Benjamini-Hochberg procedure to correct for multiple comparisons.
- `run_median_split_sensitivity(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]`
 - Performs median-split sensitivity analysis.
- `run_regularization_sensitivity(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]`
 - Performs regularization sensitivity analysis (sweeping alpha).
- `run_diagnostics_pipeline(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]`
 - Runs the full diagnostics pipeline including VIF, permutation importance, and sensitivity analysis.
- `main() -> None`
 - Entry point for the diagnostics script.

## `code/main.py`

Main pipeline orchestration.

- `aggregate_features() -> None`
 - Aggregates features from preprocessing into `data/processed/feature_matrix.csv`.
- `main() -> None`
 - Entry point for the main pipeline script. Orchestrates data loading, preprocessing, modeling, and diagnostics.