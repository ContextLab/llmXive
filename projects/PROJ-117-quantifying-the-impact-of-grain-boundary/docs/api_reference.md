# API Reference

This document details the public API for the `llmXive` grain boundary diffusivity pipeline.

## `code/utils.py`

Utility functions for logging, checksums, and random seed management.

- `setup_logging(log_level: str = "INFO") -> logging.Logger`: Configures logging.
- `compute_sha256(file_path: str) -> str`: Returns SHA-256 checksum of a file.
- `set_random_seed(seed: int)`: Sets seeds for numpy and random.
- `load_metadata(path: str) -> dict`: Loads `metadata.yaml`.
- `update_metadata_entry(path: str, key: str, value: Any)`: Updates a metadata entry.
- `save_metadata(path: str, data: dict)`: Saves metadata to YAML.

## `code/error_handling.py`

Error handling infrastructure for data validation.

- `DataInsufficiencyError(Exception)`: Raised when record count < 500.
- `check_data_sufficiency(count: int, required: int = 500) -> bool`: Returns True if count >= required.
- `exit_on_insufficiency(count: int, required: int = 500)`: Logs error and exits with code 1 if insufficient.

## `code/models/grain_boundary_record.py`

Data schema for grain boundary records.

- `GrainBoundaryRecord`: Dataclass with fields:
 - `misorientation_angle`: float
 - `sigma_value`: int
 - `boundary_plane_normal`: List[float]
 - `rodrigues_vector`: List[float]
 - `boundary_width`: float
 - `excess_volume`: float
 - `temperature`: float
 - `diffusivity`: float
 - `simulation_method`: str
 - `potential_id`: str

## `code/download.py`

Data acquisition from external sources.

- `fetch_materials_data(api_key: str, keywords: List[str], properties: List[str]) -> List[Dict]`: Fetches from Materials Project.
- `fetch_openkim_data(api_key: str, keywords: List[str]) -> List[Dict]`: Fetches from OpenKIM.
- `fetch_nist_data(keywords: List[str]) -> List[Dict]`: Fetches from NIST.
- `save_raw_data(data: List[Dict], output_dir: str)`: Saves raw structures and metadata.

## `code/geometry_parser.py`

Parsing atomistic structures and deriving GB descriptors.

- `parse_structure_file(file_path: str) -> Structure`: Parses POSAR/CIF using pymatgen.
- `extract_boundary_plane_normal(structure: Structure) -> List[float]`: Derives normal vector.
- `get_miller_indices(normal: List[float], lattice: Lattice) -> Tuple[int, int, int]`: Converts normal to Miller indices.
- `calculate_sigma_from_misorientation(angle: float) -> int`: Computes Σ value via CSL.
- `calculate_rodrigues_vector(angle: float, axis: List[float]) -> List[float]`: Encodes misorientation.
- `calculate_boundary_width(structure: Structure) -> float`: Computes slab width.
- `calculate_excess_volume(structure: Structure) -> float`: Computes excess volume.
- `extract_geometry_features(structure: Structure) -> Dict[str, Any]`: Aggregates all features.
- `parse_all_structures(input_dir: str, output_path: str)`: Processes all files in a directory.

## `code/preprocess.py`

Data cleaning and feature validation.

- `load_parsed_data(path: str) -> pd.DataFrame`: Loads parquet file.
- `validate_features(df: pd.DataFrame, required: List[str]) -> Tuple[pd.DataFrame, List[str]]`: Filters missing features.
- `tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame`: Adds simulation_method and potential_id.
- `enforce_minimum_records(df: pd.DataFrame, min_count: int = 500)`: Raises error if count < min_count.
- `save_cleaned_data(df: pd.DataFrame, path: str)`: Saves cleaned dataset.

## `code/diagnostics.py`

Collinearity analysis.

- `calculate_sigma_from_misorientation(angle: float) -> int`: Re-exports from geometry_parser.
- `compute_mutual_information(x: np.ndarray, y: np.ndarray) -> float`: Calculates MI.
- `run_collinearity_diagnostic(df: pd.DataFrame) -> Dict[str, Any]`: Runs MI between misorientation and Σ.
- `main()`: Entry point for CLI.

## `code/train.py`

Model training and evaluation.

- `load_and_prepare_data(path: str) -> Tuple[pd.DataFrame, List[str]]`: Loads data and feature list.
- `split_data(df: pd.DataFrame, test_size: float = 0.15, val_size: float = 0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]`: Splits into train/val/test.
- `tune_hyperparameters(X_train: pd.DataFrame, y_train: pd.Series) -> XGBRegressor`: Performs RandomizedSearchCV.
- `evaluate_model(model: XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]`: Computes R², RMSE, MAPE.
- `save_model_and_metrics(model: XGBRegressor, metrics: Dict, path: str)`: Saves model and metrics.

## `code/validate.py`

Validation and bias testing.

- `load_model_and_data(model_path: str, data_path: str)`: Loads model and data.
- `perform_cross_validation(model, X, y, k: int = 5) -> Dict[str, float]`: Runs k-fold CV.
- `run_regression_bias_test(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]`: Fits y_true ~ y_pred.
- `generate_report(cv_results: Dict, bias_results: Dict) -> Dict`: Generates validation report.

## `code/interpret.py`

Interpretability and sensitivity analysis.

- `load_model_and_data(model_path: str, data_path: str)`: Loads model and data.
- `generate_shap_analysis(model, X: pd.DataFrame) -> Dict`: Computes SHAP values and plots.
- `perform_sensitivity_analysis(model, X: pd.DataFrame, thresholds: List[float]) -> pd.DataFrame`: Sweeps R² thresholds.
- `main()`: Entry point for CLI.
