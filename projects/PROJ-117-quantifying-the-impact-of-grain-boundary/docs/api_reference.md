# API Reference

This document provides detailed documentation for all public APIs in the grain boundary diffusivity project.

## Configuration Modules

### `code/config/linting_config.py`

Provides configuration for linting and formatting tools.

#### Functions

- `get_ruff_command() -> str`: Returns the ruff command line string.
- `get_ruff_fix_command() -> str`: Returns the ruff fix command line string.
- `get_black_command() -> str`: Returns the black command line string.
- `get_black_check_command() -> str`: Returns the black check command line string.
- `get_ruff_config_file_content() -> str`: Returns the ruff configuration file content.
- `get_black_config_file_content() -> str`: Returns the black configuration file content.

### `code/config/threshold_config.py`

Manages R² threshold configurations for model validation.

#### Classes

- `ThresholdConfig`: Dataclass holding threshold metadata.

#### Functions

- `get_r2_threshold() -> float`: Returns the R² threshold value (default: 0.7).
- `get_threshold_justification() -> str`: Returns the justification for the threshold.
- `get_threshold_reference() -> str`: Returns the reference source for the threshold.
- `get_threshold_metadata() -> Dict`: Returns metadata about the threshold configuration.

## Core Modules

### `code/utils.py`

Shared utilities for the project.

#### Functions

- `setup_logging(log_file: str = "project.log") -> logging.Logger`: Configures and returns a logger.
- `compute_sha256(file_path: str) -> str`: Computes SHA-256 checksum of a file.
- `set_random_seed(seed: int) -> None`: Sets random seed for reproducibility.
- `load_metadata() -> Dict`: Loads metadata from `data/metadata.yaml`.
- `update_metadata_entry(key: str, value: Any) -> None`: Updates a metadata entry.
- `save_metadata() -> None`: Saves metadata to `data/metadata.yaml`.

### `code/error_handling.py`

Custom error handling for data insufficiency.

#### Classes

- `DataInsufficiencyError(Exception)`: Raised when data count is below minimum threshold.

#### Functions

- `check_data_sufficiency(count: int, min_count: int) -> bool`: Checks if count meets minimum.
- `exit_on_insufficiency(count: int, min_count: int, missing_features: List[str]) -> None`: Exits with error if insufficient.

### `code/models/grain_boundary_record.py`

Data schema for grain boundary records.

#### Classes

- `GrainBoundaryRecord`: Dataclass representing a grain boundary record with fields for misorientation, sigma value, boundary plane, diffusivity, etc.

### `code/diagnostics.py`

Collinearity and correlation diagnostics.

#### Functions

- `calculate_sigma_from_misorientation(angle: float) -> int`: Calculates Σ value from misorientation angle.
- `compute_mutual_information(data: pd.DataFrame, col1: str, col2: str) -> float`: Computes mutual information between two columns.
- `run_collinearity_diagnostic(data_path: str) -> Dict`: Runs full collinearity diagnostic and saves report.
- `main() -> None`: Entry point for diagnostics script.

### `code/download.py`

Data acquisition from external sources.

#### Functions

- `fetch_materials_project_data(keywords: List[str], properties: List[str]) -> List[Dict]`: Fetches data from Materials Project API.
- `fetch_openkim_data(keywords: List[str]) -> List[Dict]`: Fetches data from OpenKIM.
- `save_raw_data(data: List[Dict], output_dir: str) -> None`: Saves raw data files with checksums.
- `main() -> None`: Entry point for download script.

### `code/geometry_parser.py`

Geometry feature extraction from crystal structures.

#### Functions

- `calculate_sigma_from_misorientation(angle: float) -> int`: Calculates Σ value.
- `calculate_rodrigues_vector(rotation_matrix: np.ndarray) -> List[float]`: Converts rotation matrix to Rodrigues vector.
- `get_miller_indices(plane_normal: np.ndarray, lattice: Lattice) -> List[int]`: Converts plane normal to Miller indices.
- `extract_boundary_plane_normal(structure: Structure) -> np.ndarray`: Extracts boundary plane normal.
- `calculate_boundary_width(structure: Structure) -> float`: Calculates boundary width.
- `calculate_excess_volume(structure: Structure, bulk_density: float) -> float`: Calculates excess volume.
- `parse_structure_file(file_path: str) -> Structure`: Parses POSCAR/CIF file.
- `extract_geometry_features(structure: Structure) -> Dict`: Extracts all geometry features.
- `parse_all_structures(input_dir: str, output_path: str) -> None`: Parses all structures in directory.
- `main() -> None`: Entry point for geometry parser script.

### `code/preprocess.py`

Data cleaning and validation.

#### Functions

- `load_parsed_data(input_path: str) -> pd.DataFrame`: Loads parsed geometry data.
- `validate_features(df: pd.DataFrame, required: List[str]) -> pd.DataFrame`: Filters rows with missing required features.
- `tag_metadata_features(df: pd.DataFrame, metadata_fields: List[str]) -> pd.DataFrame`: Tags metadata columns.
- `enforce_minimum_records(df: pd.DataFrame, min_count: int) -> pd.DataFrame`: Ensures minimum record count.
- `save_cleaned_data(df: pd.DataFrame, output_path: str) -> None`: Saves cleaned dataset.
- `main() -> None`: Entry point for preprocessing script.

### `code/train.py`

Model training and evaluation.

#### Functions

- `load_and_prepare_data(data_path: str) -> Tuple[np.ndarray, np.ndarray]`: Loads and prepares data for training.
- `split_data(X: np.ndarray, y: np.ndarray) -> Tuple`: Splits data into train/val/test sets (70/15/15).
- `tune_hyperparameters(X_train, y_train, X_val, y_val) -> Tuple`: Performs RandomizedSearchCV for XGBoost.
- `evaluate_model(model, X_test, y_test) -> Dict`: Evaluates model and returns metrics (R², RMSE, MAPE).
- `save_model_and_metrics(model, metrics, model_path: str, report_path: str) -> None`: Saves model and metrics.
- `main() -> None`: Entry point for training script.

### `code/validate.py`

Model validation and bias testing.

#### Functions

- `load_model_and_data(model_path: str, data_path: str) -> Tuple`: Loads model and data.
- `perform_cross_validation(model, X, y, k: int) -> Dict`: Performs k-fold cross-validation.
- `run_regression_bias_test(y_true, y_pred) -> Dict`: Runs regression bias test with Bonferroni correction.
- `generate_report(cv_metrics: Dict, bias_results: Dict) -> Dict`: Generates validation report.
- `main() -> None`: Entry point for validation script.

### `code/interpret.py`

SHAP analysis and sensitivity analysis.

#### Functions

- `load_model_and_data(model_path: str, data_path: str) -> Tuple`: Loads model and data.
- `generate_shap_analysis(model, X, output_path: str) -> str`: Generates SHAP summary plot.
- `perform_sensitivity_analysis(model, X, y, threshold_range: List[float]) -> pd.DataFrame`: Performs sensitivity analysis on R² threshold.
- `main() -> None`: Entry point for interpretability script.

### `code/optimization_utils.py`

Vectorized operations for performance.

#### Functions

- `vectorize_miller_indices_calculation(...)`: Vectorized Miller indices calculation.
- `vectorize_sigma_calculation(...)`: Vectorized Σ value calculation.
- `vectorize_rodrigues_encoding(...)`: Vectorized Rodrigues encoding.
- `vectorize_feature_scaling(...)`: Vectorized feature scaling.
- `vectorize_missing_value_imputation(...)`: Vectorized missing value imputation.
- `vectorize_diffusivity_calculation(...)`: Vectorized diffusivity calculation.
- `vectorize_correlation_matrix(...)`: Vectorized correlation matrix.
- `vectorize_outlier_detection(...)`: Vectorized outlier detection.
- `benchmark_vectorization(...)`: Benchmarks vectorized operations.
- `ensure_vectorized_operations(...)`: Ensures operations are vectorized.

### `code/setup_project.py`

Project initialization.

#### Functions

- `create_directory(path: str) -> None`: Creates directory if not exists.
- `main() -> None`: Entry point for project setup.

### `code/setup_env.py`

Environment setup and API key validation.

#### Functions

- `load_environment() -> bool`: Loads.env file.
- `validate_api_keys() -> bool`: Validates required API keys.
- `main() -> None`: Entry point for environment setup.

### `code/update_state.py`

State management and hash verification.

#### Functions

- `compute_sha256(file_path: str) -> str`: Computes SHA-256 hash.
- `scan_directory(dir_path: str) -> Dict`: Scans directory for files.
- `load_state(state_path: str) -> Dict`: Loads state file.
- `save_state(state: Dict, state_path: str) -> None`: Saves state file.
- `verify_hashes(state: Dict) -> bool`: Verifies file hashes.
- `main() -> None`: Entry point for state update script.

### `code/validate_quickstart.py`

Quickstart validation script.

#### Functions

- `check_directory_structure() -> bool`: Validates directory structure.
- `check_required_files() -> bool`: Checks for required files.
- `check_dependencies() -> bool`: Checks installed dependencies.
- `check_pipeline_scripts() -> bool`: Validates pipeline scripts exist.
- `run_pipeline_step(step_name: str) -> bool`: Runs a pipeline step.
- `check_output_artifacts() -> bool`: Checks for output artifacts.
- `validate_output_content() -> bool`: Validates output content.
- `main() -> None`: Entry point for quickstart validation.
