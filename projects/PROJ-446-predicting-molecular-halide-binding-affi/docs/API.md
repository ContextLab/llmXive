# Project API Reference

This document provides a comprehensive reference for all public functions and classes within the `code/` directory of the `PROJ-446-predicting-molecular-halide-binding-affi` project.

## Directory Structure

- `code/`: Main pipeline scripts
- `code/utils/`: Shared utilities (configuration, logging, validation, state management)

---

## `code/01_data_ingestion.py`

Main module for downloading, parsing, and cleaning experimental halide binding data.

### Functions

#### `parse_smiles(smiles_string: str) -> Optional[rdkit.Chem.Mol]`
Parses a SMILES string into an RDKit molecule object.
- **Args**:
 - `smiles_string`: The SMILES string representation of the molecule.
- **Returns**:
 - An RDKit `Mol` object if valid, `None` otherwise.

#### `parse_inchi(inchi_string: str) -> Optional[rdkit.Chem.Mol]`
Parses an InChI string into an RDKit molecule object.
- **Args**:
 - `inchi_string`: The InChI string representation of the molecule.
- **Returns**:
 - An RDKit `Mol` object if valid, `None` otherwise.

#### `standardize_affinity_value(value: float, unit: str) -> float`
Standardizes binding affinity values to a common unit (log K).
- **Args**:
 - `value`: The numerical affinity value.
 - `unit`: The unit of the value (e.g., "log K", "ΔG", "kcal/mol").
- **Returns**:
 - The standardized value as `log K`.

#### `validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame`
Validates and cleans the raw dataset, filtering out invalid structures and missing values.
- **Args**:
 - `df`: The raw pandas DataFrame.
- **Returns**:
 - A cleaned DataFrame with valid SMILES, InChI, and standardized affinity values.

#### `scrape_nist_pubchem() -> pd.DataFrame`
Scrapes halide binding data from NIST and PubChem sources.
- **Returns**:
 - A pandas DataFrame containing raw binding data.
- **Note**: Implements exponential backoff and rate limiting (2s delay).

#### `filter_hosts_with_multiple_halides(df: pd.DataFrame) -> pd.DataFrame`
Filters the dataset to retain only hosts with measurements for at least 3 different halides.
- **Args**:
 - `df`: The input DataFrame.
- **Returns**:
 - A filtered DataFrame.

#### `run_data_pipeline() -> pd.DataFrame`
Executes the full data ingestion pipeline: scraping, cleaning, and filtering.
- **Returns**:
 - The final processed DataFrame ready for feature engineering.

---

## `code/02_save_processed_data.py`

Module for saving the processed dataset to disk, handling both real and simulated data modes.

### Functions

#### `check_simulated_mode() -> bool`
Checks if the project is running in simulated data mode.
- **Returns**:
 - `True` if `data/simulated/state.json` exists and `SIMULATED_MODE` is True.

#### `get_source_dataframe() -> pd.DataFrame`
Retrieves the source DataFrame based on the current mode (real or simulated).
- **Returns**:
 - The appropriate DataFrame.

#### `save_processed_dataset(df: pd.DataFrame, output_path: str) -> None`
Saves the processed DataFrame to a CSV file with schema compliance.
- **Args**:
 - `df`: The DataFrame to save.
 - `output_path`: The destination file path.

#### `main()`
Entry point for the script. Orchestrates loading, validation, and saving of the processed dataset.

---

## `code/03_model_training.py`

Module for training and evaluating machine learning models with host-identity splitting.

### Classes

#### `HostIdentityKFold`
Custom K-Fold cross-validator that ensures no host molecule appears in both train and validation sets within a fold.
- **Methods**:
 - `split(X, y, groups)`: Yields train/test indices.

### Functions

#### `load_preprocessed_data() -> Tuple[pd.DataFrame, pd.Series]`
Loads the preprocessed dataset and separates features from the target.
- **Returns**:
 - Tuple of (Features DataFrame, Target Series).

#### `train_and_evaluate_model(model, X_train, X_test, y_train, y_test) -> Dict[str, float]`
Trains a model and evaluates it using R² and RMSE.
- **Args**:
 - `model`: The scikit-learn model instance.
 - `X_train`, `X_test`: Training and testing features.
 - `y_train`, `y_test`: Training and testing targets.
- **Returns**:
 - Dictionary containing `r2` and `rmse` metrics.

#### `run_random_forest_training() -> Dict[str, Any]`
Trains a Random Forest model with k-fold cross-validation.
- **Returns**:
 - Dictionary containing model artifacts, metrics, and feature importances.

#### `run_gradient_boosting_training() -> Dict[str, Any]`
Trains a Gradient Boosting model with k-fold cross-validation.
- **Returns**:
 - Dictionary containing model artifacts, metrics, and feature importances.

#### `save_model_artifacts(results: Dict[str, Any], output_path: str) -> None`
Saves model training results to a JSON file.
- **Args**:
 - `results`: The results dictionary.
 - `output_path`: The destination file path.

#### `main()`
Entry point for the script. Orchestrates training for both models and saving artifacts.

---

## `code/04_feature_analysis.py`

Module for analyzing feature stability and generating partial dependence plots.

### Functions

#### `load_preprocessed_data() -> Tuple[pd.DataFrame, pd.Series]`
Loads the preprocessed dataset (alias from model_training).

#### `get_feature_columns(df: pd.DataFrame) -> List[str]`
Identifies feature columns in the DataFrame.
- **Returns**:
 - List of feature column names.

#### `run_feature_stability_analysis(model, df: pd.DataFrame, n_bootstrap: int = 100) -> Dict[str, float]`
Performs bootstrap resampling to calculate feature stability (Coefficient of Variation).
- **Args**:
 - `model`: The trained model.
 - `df`: The input DataFrame.
 - `n_bootstrap`: Number of bootstrap iterations.
- **Returns**:
 - Dictionary mapping features to their CV scores.

#### `check_physical_plausibility(feature_importance: Dict[str, float]) -> Dict[str, Any]`
Checks if the sign of the top feature's coefficient aligns with physical principles.
- **Args**:
 - `feature_importance`: Dictionary of feature importances.
- **Returns**:
 - Dictionary with plausibility status and details.

#### `save_feature_analysis_results(results: Dict[str, Any], output_path: str) -> None`
Saves feature analysis results to a JSON file.

#### `generate_partial_dependence_plots(model, df: pd.DataFrame, features: List[str]) -> None`
Generates partial dependence plots for specified features.
- **Args**:
 - `model`: The trained model.
 - `df`: The input DataFrame.
 - `features`: List of feature names to plot.
- **Output**:
 - Saves PNG files to `docs/paper/figures/`.

#### `main()`
Entry point for the script. Runs stability analysis, plausibility checks, and plot generation.

---

## `code/05_statistical_reporting.py`

Module for statistical reporting, including bootstrap confidence intervals and power analysis.

### Functions

#### `load_model_metrics() -> Dict[str, Any]`
Loads model metrics from `data/processed/model_runs.json`.

#### `get_halide_counts(df: pd.DataFrame) -> Dict[str, int]`
Counts the number of samples per halide group.

#### `run_power_analysis(counts: Dict[str, int]) -> Dict[str, Any]`
Checks if the sample size (N ≥ 10) is sufficient for statistical power.
- **Returns**:
 - Dictionary with power status and group counts.

#### `save_statistical_summary(summary: Dict[str, Any], output_path: str) -> None`
Saves statistical summary to a JSON file.

#### `run_statistical_analysis(metrics: Dict[str, Any]) -> Dict[str, Any]`
Computes bootstrap confidence intervals for performance differences between halide groups.
- **Returns**:
 - Dictionary containing CIs and comparison results.

#### `generate_report_section(summary: Dict[str, Any]) -> str`
Generates a Markdown section for the final report.
- **Returns**:
 - Markdown string.

#### `main()`
Entry point for the script. Orchestrates statistical analysis and report generation.

---

## `code/utils/config.py`

Utility module for project configuration.

### Functions

#### `get_path(key: str) -> Path`
Retrieves a configured path by key.
- **Args**:
 - `key`: Configuration key (e.g., "data_root", "code_root").

#### `get_data_path() -> Path`
Returns the root data directory.

#### `get_code_path() -> Path`
Returns the root code directory.

#### `set_seed(seed: int) -> None`
Sets the random seed for reproducibility.

#### `get_solvent_list() -> List[str]`
Returns the list of allowed solvents.

#### `is_simulated_mode() -> bool`
Checks if the project is in simulated mode.

#### `set_simulated_mode(mode: bool) -> None`
Sets the simulated mode flag.

---

## `code/utils/logger.py`

Utility module for logging.

### Classes

#### `JsonFormatter(logging.Formatter)`
Custom formatter that outputs logs in JSON format.

### Functions

#### `get_logger(name: str) -> logging.Logger`
Retrieves or creates a logger with JSON formatting and rotating file handler.

#### `log_with_extra(logger: logging.Logger, level: int, msg: str, extra: Dict[str, Any]) -> None`
Logs a message with additional context fields.

---

## `code/utils/state_manager.py`

Utility module for managing project state and artifact hashing.

### Functions

#### `calculate_file_hash(file_path: Path) -> str`
Calculates the SHA-256 hash of a file.

#### `calculate_directory_hash(dir_path: Path) -> Dict[str, str]`
Calculates hashes for all files in a directory.

#### `load_state_yaml() -> Dict[str, Any]`
Loads the `state.yaml` file.

#### `save_state_yaml(state: Dict[str, Any]) -> None`
Saves the state dictionary to `state.yaml`.

#### `update_artifact_hash(path: Path) -> None`
Updates the hash for a specific artifact in the state.

#### `set_simulated_mode(mode: bool) -> None`
Updates the simulated mode flag in the state.

#### `get_simulated_mode() -> bool`
Retrieves the simulated mode flag from the state.

#### `generate_state_for_directory(dir_path: Path) -> Dict[str, str]`
Generates a state dictionary for a directory's contents.

#### `init_project_state() -> None`
Initializes the project state file.

#### `get_project_state_path() -> Path`
Returns the path to the `state.yaml` file.

---

## `code/utils/validators.py`

Utility module for data validation.

### Functions

#### `load_schema() -> Dict[str, Any]`
Loads the dataset schema from `dataset.schema.yaml`.

#### `validate_smiles(smiles: str) -> bool`
Validates a SMILES string.

#### `validate_column_types(df: pd.DataFrame) -> bool`
Validates column types in a DataFrame against the schema.

#### `validate_constraints(df: pd.DataFrame) -> bool`
Validates data constraints (e.g., non-null, ranges).

#### `validate_dataset(df: pd.DataFrame) -> bool`
Runs full validation (schema, types, constraints).

#### `ensure_schema_file_exists() -> None`
Ensures the schema file exists; creates it if missing.

---

## `code/setup_linting.py`

Module for configuring linting and formatting tools.

### Functions

#### `ensure_config_files() -> None`
Creates configuration files for ruff and black if they don't exist.

#### `run_lint() -> int`
Runs the linter (ruff) and returns the exit code.

#### `run_format() -> int`
Runs the formatter (black) and returns the exit code.

#### `main()`
Entry point for setting up and running lint/format checks.

---

## `code/setup_project.py`

Module for project initialization.

### Functions

#### `main()`
Entry point for project setup (directory creation, dependency installation).

---

## `code/00_create_directories.py`

Module for creating project directory structure.

### Functions

#### `main()`
Entry point that creates required directories (`code/`, `data/`, `docs/`, etc.).

---

## `code/00_create_state.py`

Module for initializing project state.

### Functions

#### `main()`
Entry point that initializes `state.yaml` and updates artifact hashes.

---

## `code/04_create_data_dirs.py`

Module for creating data subdirectories.

### Functions

#### `create_directories() -> None`
Creates `data/raw/`, `data/processed/`, `data/simulated/`, and `docs/paper/`.

#### `main()`
Entry point.

---

## `code/05_feature_summary.py`

Module for generating feature summary tables.

### Functions

#### `load_feature_stability_results() -> Dict[str, float]`
Loads feature stability results.

#### `load_physical_plausibility_results() -> Dict[str, Any]`
Loads physical plausibility results.

#### `generate_summary_table(stability: Dict[str, float], plausibility: Dict[str, Any]) -> pd.DataFrame`
Generates a summary DataFrame mapping features to hypotheses.

#### `save_summary_table(df: pd.DataFrame, output_path: str) -> None`
Saves the summary table to CSV.

#### `main()`
Entry point.

---

## `code/06_generate_final_report.py`

Module for generating the final research report.

### Functions

#### `load_statistical_summary() -> Dict[str, Any]`
Loads statistical summary data.

#### `load_feature_summary() -> pd.DataFrame`
Loads feature summary table.

#### `load_model_artifacts() -> Dict[str, Any]`
Loads model artifacts.

#### `generate_report_header() -> str`
Generates the report header.

#### `generate_methods_section() -> str`
Generates the methods section.

#### `generate_results_section() -> str`
Generates the results section.

#### `generate_discussion_section() -> str`
Generates the discussion section.

#### `generate_report_content() -> str`
Assembles the full report content.

#### `save_report(content: str, output_path: str) -> None`
Saves the report to a Markdown file.

#### `main()`
Entry point.

---

## `code/06_save_feature_outputs.py`

Module for saving final feature analysis outputs.

### Functions

#### `load_json_safe(path: str) -> Optional[Dict]`
Loads a JSON file safely.

#### `load_csv_safe(path: str) -> Optional[pd.DataFrame]`
Loads a CSV file safely.

#### `ensure_figures_directory() -> None`
Ensures the figures directory exists.

#### `move_figures(source: Path, dest: Path) -> None`
Moves generated figures to the final destination.

#### `aggregate_results() -> Dict[str, Any]`
Aggregates all analysis results.

#### `save_final_outputs() -> None`
Saves all final outputs (JSON, CSV, figures).

#### `main()`
Entry point.