# Quantifying the Impact of Grain Boundary Character on Diffusivity

This project implements an automated science pipeline to download atomistic simulation datasets, extract grain-boundary descriptors, and train a gradient-boosted tree model to predict atomic diffusivity.

## Project Structure

```
.
├── code/ # Python implementation modules
│ ├── config/ # Configuration utilities
│ ├── models/ # Data schemas
│ ├── utils.py # Shared utilities
│ ├── download.py # Data acquisition
│ ├── geometry_parser.py # Geometry feature extraction
│ ├── preprocess.py # Data cleaning & validation
│ ├── train.py # Model training
│ ├── validate.py # Model validation
│ ├── interpret.py # SHAP analysis & sensitivity
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data (POSCAR, CIF)
│ ├── processed/ # Parsed and cleaned datasets
│ └── metadata.yaml # Data provenance schema
├── models/ # Trained model artifacts
├── artifacts/
│ ├── reports/ # Diagnostic and validation reports
│ └── figures/ # SHAP plots and sensitivity tables
├── specs/ # Design documents
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Data Schema

The project uses a `GrainBoundaryRecord` dataclass to represent grain boundary data. The schema is defined in `code/models/grain_boundary_record.py`.

### GrainBoundaryRecord Fields

| Field | Type | Description |
|-------|------|-------------|
| `material_id` | str | Unique identifier for the material |
| `misorientation_angle` | float | Angle of misorientation in degrees |
| `sigma_value` | int | Coincidence Site Lattice (Σ) value |
| `boundary_plane_normal` | List[int] | Miller indices (hkl) of the boundary plane |
| `rodrigues_vector` | List[float] | Rodrigues vector representation of misorientation |
| `boundary_width` | float | Width of the grain boundary in Å |
| `excess_volume` | float | Excess volume at the boundary in Å³/atom |
| `temperature` | float | Temperature in Kelvin |
| `composition` | str | Chemical composition string |
| `diffusivity` | float | Atomic diffusivity (target variable) |
| `simulation_method` | str | Method used (DFT, MD, KMC) |
| `potential_id` | str | Interatomic potential identifier |
| `source` | str | Data source (Materials Project, OpenKIM, NIST) |
| `checksum` | str | SHA-256 checksum of the raw file |
| `retrieval_date` | str | Date of data retrieval |

### Metadata Schema (`data/metadata.yaml`)

The `metadata.yaml` file tracks data provenance:

```yaml
source: Materials Project | OpenKIM | NIST
version_tag: v1.0.0
checksum: <sha256_hash>
retrieval_date: YYYY-MM-DD
record_count: <number>
```

## API Usage

The project provides several Python modules for different stages of the pipeline. Below are examples of how to use the key APIs.

### Data Download (`code/download.py`)

```python
from download import fetch_materials_project_data, fetch_openkim_data, save_raw_data

# Fetch data from Materials Project
mp_data = fetch_materials_project_data(
 keywords=["grain boundary", "bicrystal"],
 properties=["diffusivity"]
)

# Fetch data from OpenKIM
ok_data = fetch_openkim_data(
 keywords=["grain boundary"]
)

# Save raw data files with checksums
save_raw_data(mp_data, "data/raw/mp_grain_boundaries/")
save_raw_data(ok_data, "data/raw/openkim_grain_boundaries/")
```

### Geometry Parsing (`code/geometry_parser.py`)

```python
from geometry_parser import parse_structure_file, extract_geometry_features

# Parse a POSAR or CIF file
structure = parse_structure_file("data/raw/sample_POSCAR")

# Extract geometry features
features = extract_geometry_features(structure)
# Returns: {
# 'misorientation_angle': float,
# 'sigma_value': int,
# 'boundary_plane_normal': [h, k, l],
# 'rodrigues_vector': [rx, ry, rz],
# 'boundary_width': float,
# 'excess_volume': float
# }
```

### Preprocessing (`code/preprocess.py`)

```python
from preprocess import load_parsed_data, validate_features, tag_metadata_features, enforce_minimum_records, save_cleaned_data

# Load parsed data
df = load_parsed_data("data/processed/parsed_geometry.parquet")

# Validate required features
valid_df = validate_features(df, required=['misorientation_angle', 'sigma_value', 'diffusivity'])

# Tag metadata features
tagged_df = tag_metadata_features(valid_df, metadata_fields=['simulation_method', 'potential_id'])

# Enforce minimum record count (n >= 500)
final_df = enforce_minimum_records(tagged_df, min_count=500)

# Save cleaned dataset
save_cleaned_data(final_df, "data/processed/cleaned_dataset.parquet")
```

### Model Training (`code/train.py`)

```python
from train import load_and_prepare_data, split_data, tune_hyperparameters, evaluate_model, save_model_and_metrics

# Load and prepare data
X, y = load_and_prepare_data("data/processed/cleaned_dataset.parquet")

# Split data (70/15/15)
X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)

# Hyperparameter tuning with RandomizedSearchCV
best_model, best_params = tune_hyperparameters(X_train, y_train, X_val, y_val)

# Evaluate on test set
metrics = evaluate_model(best_model, X_test, y_test)
# Returns: {'r2': float, 'rmse': float, 'mape': float}

# Save model and metrics
save_model_and_metrics(best_model, metrics, "models/best_model.json", "artifacts/reports/training_metrics.json")
```

### Validation (`code/validate.py`)

```python
from validate import load_model_and_data, perform_cross_validation, run_regression_bias_test, generate_report

# Load model and data
model, X, y = load_model_and_data("models/best_model.json", "data/processed/cleaned_dataset.parquet")

# Perform 5-fold cross-validation
cv_metrics = perform_cross_validation(model, X, y, k=5)

# Run regression bias test
bias_results = run_regression_bias_test(y, model.predict(X))

# Generate validation report
report = generate_report(cv_metrics, bias_results)
# Saves to: artifacts/reports/validation_report.json
```

### Interpretability (`code/interpret.py`)

```python
from interpret import load_model_and_data, generate_shap_analysis, perform_sensitivity_analysis

# Load model and data
model, X, y = load_model_and_data("models/best_model.json", "data/processed/cleaned_dataset.parquet")

# Generate SHAP analysis
shap_plot_path = generate_shap_analysis(model, X, "artifacts/figures/shap_summary.png")

# Perform sensitivity analysis on R² threshold
sensitivity_table = perform_sensitivity_analysis(model, X, y, threshold_range=[0.5, 0.7, 0.8, 0.9])
# Saves to: artifacts/reports/threshold-variation-table.csv
```

### Diagnostics (`code/diagnostics.py`)

```python
from diagnostics import run_collinearity_diagnostic

# Run collinearity diagnostic on raw dataset
result = run_collinearity_diagnostic("data/processed/parsed_geometry.parquet")
# Calculates Mutual Information between misorientation angle and Σ value
# Saves to: artifacts/reports/collinearity_diagnostic.json
```

## Running the Pipeline

1. **Setup Environment**
 ```bash
 pip install -r requirements.txt
 python code/setup_env.py
 ```

2. **Download Data**
 ```bash
 python code/download.py
 ```

3. **Parse Geometry**
 ```bash
 python code/geometry_parser.py
 ```

4. **Preprocess Data**
 ```bash
 python code/preprocess.py
 ```

5. **Train Model**
 ```bash
 python code/train.py
 ```

6. **Validate Model**
 ```bash
 python code/validate.py
 ```

7. **Interpret Results**
 ```bash
 python code/interpret.py
 ```

## Requirements

- Python 3.8+
- pandas, numpy, scikit-learn, xgboost, shap, matplotlib, requests, pymatgen, python-dotenv

See `requirements.txt` for exact versions.

## License

This project is licensed under the MIT License.
