# API Reference

This document provides detailed API documentation for the core modules in the project.

## `code/download.py`

### `fetch_materials_project_data(keywords, properties)`

Fetches grain boundary and diffusivity data from the Materials Project API.

**Parameters:**
- `keywords` (list): Search keywords (e.g., `["grain boundary", "bicrystal"]`)
- `properties` (list): Properties to retrieve (e.g., `["diffusivity"]`)

**Returns:**
- `dict`: JSON response containing material records.

**Raises:**
- `requests.RequestException`: If API call fails.

### `fetch_openkim_data(query_params)`

Fetches interatomic potential and simulation data from OpenKIM.

### `save_raw_data(data, output_path)`

Saves raw JSON data to disk and computes SHA-256 checksum.

**Parameters:**
- `data` (dict): Data to save.
- `output_path` (str): Path to output file.

---

## `code/geometry_parser.py`

### `parse_structure_file(file_path)`

Parses a crystal structure file (POSCAR, CIF) using `pymatgen`.

**Parameters:**
- `file_path` (str): Path to structure file.

**Returns:**
- `Structure`: `pymatgen` Structure object.

### `calculate_sigma_value(misorientation_angle)`

Calculates the Σ value using the Coincidence Site Lattice (CSL) definition.

**Parameters:**
- `misorientation_angle` (float): Angle in degrees.

**Returns:**
- `int`: Σ value.

### `calculate_miller_indices(normal_vector, lattice)`

Converts a normal vector to Miller indices (hkl).

**Parameters:**
- `normal_vector` (list): [x, y, z] vector.
- `lattice`: `pymatgen` Lattice object.

**Returns:**
- `str`: Miller indices as "h,k,l".

### `calculate_rodrigues_vector(rotation_matrix)`

Converts a rotation matrix to a Rodrigues vector.

### `extract_boundary_plane_normal(structure)`

Extracts the boundary plane normal from a bicrystal structure.

### `calculate_boundary_width(structure)`

Calculates the boundary width from simulation cell dimensions.

### `calculate_excess_volume(structure)`

Calculates excess volume per unit area.

---

## `code/preprocess.py`

### `load_parsed_data(file_path)`

Loads parsed geometry data from a Parquet file.

### `validate_required_features(data, required_features)`

Validates that all required features are present.

### `filter_records(data, missing_features)`

Filters out records with missing required features.

### `tag_metadata_features(data)`

Tags `simulation_method` and `potential_id` as metadata features.

---

## `code/train.py`

### `load_data(file_path)`

Loads cleaned dataset from Parquet.

### `prepare_features(data)`

Prepares feature matrix and target vector.

### `split_data(data, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)`

Splits data into train/validation/test sets.

### `tune_and_train(X_train, y_train)`

Performs RandomizedSearchCV for XGBoost hyperparameter tuning.

**Returns:**
- `XGBRegressor`: Best trained model.

### `evaluate_model(model, X_test, y_test)`

Evaluates model on test set and returns R², RMSE, MAPE.

### `save_artifacts(model, metrics, output_dir)`

Saves model and metrics to disk.

---

## `code/validate.py`

### `perform_cross_validation(model, data, k=5)`

Performs k-fold cross-validation.

### `regression_bias_test(y_true, y_pred)`

Tests for regression bias (y_true ~ y_pred).

### `apply_bonferroni_correction(p_values, alpha=0.01)`

Applies Bonferroni correction to p-values.

### `generate_validation_report(metrics, bias_test)`

Generates validation report dictionary.

---

## `code/interpret.py`

### `generate_shap_analysis(model, data)`

Generates SHAP summary plot and feature importance.

### `perform_sensitivity_analysis(model, data, threshold_range)`

Sweeps R² threshold and calculates pass rates.

### `generate_threshold_justification_report()`

Generates a one-line justification for R² ≥ 0.7 threshold.

---

## `code/diagnostics.py`

### `calculate_sigma_value(misorientation_angle)`

Calculates Σ value (alias for geometry_parser version).

### `compute_mutual_information(data, feature1, feature2)`

Computes Mutual Information between two features.

### `run_diagnostics(data)`

Runs full diagnostic suite and saves report.

---

## `code/utils.py`

### `compute_sha256(file_path)`

Computes SHA-256 checksum of a file.

### `setup_logging(log_file)`

Sets up logging to file and console.

### `set_random_seed(seed)`

Sets random seed for reproducibility.

### `raise_data_insufficiency(retrieved_count, required_count, missing_features)`

Raises `DataInsufficiencyError` with detailed message.
