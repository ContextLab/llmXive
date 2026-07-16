# API Reference

This document provides detailed API documentation for the `code/` modules in the Grain Boundary Diffusivity pipeline.

## Module: `download`

### `fetch_materials_project_data(keywords, properties)`

Fetches grain boundary structures from the Materials Project API.

**Parameters**:
- `keywords` (List[str]): Search keywords (e.g., `["grain boundary", "bicrystal"]`)
- `properties` (List[str]): Properties to filter by (e.g., `["diffusivity"]`)

**Returns**:
- `List[Dict]`: List of record dictionaries containing structure data and metadata

**Raises**:
- `ValueError`: If API key is missing or invalid
- `ConnectionError`: If API request fails

**Example**:
```python
data = fetch_materials_project_data(
 keywords=["grain boundary"],
 properties=["diffusivity"]
)
```

### `fetch_openkim_data(keywords)`

Fetches grain boundary structures from OpenKIM.

**Parameters**:
- `keywords` (List[str]): Search keywords

**Returns**:
- `List[Dict]`: List of record dictionaries

### `save_raw_data(mp_data, kim_data, output_dir)`

Saves raw data files with SHA-256 checksums.

**Parameters**:
- `mp_data` (List[Dict]): Materials Project data
- `kim_data` (List[Dict]): OpenKIM data
- `output_dir` (str): Output directory path

**Side Effects**:
- Writes POSCAR/CIF files to `output_dir/`
- Updates `data/metadata.yaml` with checksums

---

## Module: `geometry_parser`

### `parse_structure_file(file_path)`

Parses a crystallographic structure file (POSCAR or CIF).

**Parameters**:
- `file_path` (str): Path to structure file

**Returns**:
- `pymatgen.Structure`: Parsed structure object

### `extract_geometry_features(structure)`

Extracts all geometric features from a grain boundary structure.

**Parameters**:
- `structure` (pymatgen.Structure): Input structure

**Returns**:
- `Dict[str, Any]`: Dictionary containing:
 - `misorientation_angle` (float)
 - `sigma_value` (int)
 - `boundary_plane_normal` (Tuple[int, int, int])
 - `rodrigues_vector` (Tuple[float, float, float])
 - `boundary_width` (float)
 - `excess_volume` (float)

### `calculate_sigma_from_misorientation(angle_degrees)`

Calculates Σ value from misorientation angle using CSL definition.

**Parameters**:
- `angle_degrees` (float): Misorientation angle in degrees

**Returns**:
- `int`: Σ value

### `calculate_rodrigues_vector(rotation_matrix)`

Converts rotation matrix to Rodrigues vector representation.

**Parameters**:
- `rotation_matrix` (np.ndarray): 3x3 rotation matrix

**Returns**:
- `Tuple[float, float, float]`: Rodrigues vector components

### `get_miller_indices(normal_vector, lattice)`

Converts a normal vector to Miller indices.

**Parameters**:
- `normal_vector` (np.ndarray): Normal vector components
- `lattice` (pymatgen.Lattice): Lattice object

**Returns**:
- `Tuple[int, int, int]`: Miller indices (h, k, l)

---

## Module: `preprocess`

### `load_parsed_data(file_path)`

Loads parsed geometry data from Parquet file.

**Parameters**:
- `file_path` (str): Path to parquet file

**Returns**:
- `pd.DataFrame`: DataFrame with parsed features

### `validate_features(df, required_features)`

Validates that all required features are present and non-null.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame
- `required_features` (List[str]): List of required column names

**Returns**:
- `Tuple[pd.DataFrame, List[str]]`: Validated DataFrame and list of missing features

### `tag_metadata_features(df)`

Tags metadata columns (simulation_method, potential_id) for special handling.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame

**Returns**:
- `pd.DataFrame`: DataFrame with tagged metadata

### `enforce_minimum_records(df, min_records)`

Ensures dataset meets minimum record count requirement.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame
- `min_records` (int): Minimum required records

**Raises**:
- `DataInsufficiencyError`: If record count < min_records

---

## Module: `train`

### `load_and_prepare_data(file_path, target, test_size, val_size)`

Loads data and performs train/validation/test split.

**Parameters**:
- `file_path` (str): Path to cleaned dataset
- `target` (str): Target column name
- `test_size` (float): Test split fraction
- `val_size` (float): Validation split fraction

**Returns**:
- `Tuple[np.ndarray,...]`: (X_train, X_val, X_test, y_train, y_val, y_test)

### `tune_hyperparameters(X_train, y_train, X_val, y_val, param_grid)`

Performs RandomizedSearchCV for XGBoost hyperparameter tuning.

**Parameters**:
- `X_train`, `y_train`: Training data
- `X_val`, `y_val`: Validation data
- `param_grid` (Dict): Hyperparameter search space

**Returns**:
- `Tuple[XGBRegressor, Dict]`: Best model and parameters

### `evaluate_model(model, X_test, y_test)`

Evaluates model performance on test set.

**Parameters**:
- `model`: Trained XGBoost model
- `X_test`, `y_test`: Test data

**Returns**:
- `Dict[str, float]`: Metrics dictionary (r2, rmse, mape)

---

## Module: `diagnostics`

### `compute_mutual_information(x, y)`

Computes mutual information between two variables.

**Parameters**:
- `x`, `y` (np.ndarray): Input arrays

**Returns**:
- `float`: Mutual information score

### `run_collinearity_diagnostic(data_path)`

Runs full collinearity diagnostic on dataset.

**Parameters**:
- `data_path` (str): Path to dataset

**Returns**:
- `Dict[str, Any]`: Diagnostic report including MI scores

---

## Module: `validate`

### `perform_cross_validation(model, X, y, n_folds)`

Performs k-fold cross-validation.

**Parameters**:
- `model`: Trained model
- `X`, `y`: Data
- `n_folds` (int): Number of folds

**Returns**:
- `Dict[str, float]`: Mean and std of R², RMSE, MAPE

### `run_regression_bias_test(y_true, y_pred, alpha)`

Runs regression bias test with Bonferroni correction.

**Parameters**:
- `y_true`, `y_pred`: True and predicted values
- `alpha` (float): Adjusted significance level

**Returns**:
- `Dict[str, float]`: Intercept, slope, p-values

---

## Module: `interpret`

### `generate_shap_analysis(model, X_test)`

Generates SHAP feature importance analysis.

**Parameters**:
- `model`: Trained model
- `X_test`: Test features

**Returns**:
- `Dict[str, Any]`: SHAP values and summary statistics

### `perform_sensitivity_analysis(model, X_test, y_test, thresholds)`

Performs sensitivity analysis across R² thresholds.

**Parameters**:
- `model`: Trained model
- `X_test`, `y_test`: Test data
- `thresholds` (List[float]): R² thresholds to evaluate

**Returns**:
- `pd.DataFrame`: Sensitivity table with pass rates
