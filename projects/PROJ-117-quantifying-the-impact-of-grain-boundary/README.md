# Quantifying the Impact of Grain Boundary Character on Diffusivity

**Project ID**: PROJ-117-quantifying-the-impact-of-grain-boundary

This project implements an automated science pipeline to quantify the relationship between grain boundary character (misorientation, boundary plane, Σ value) and atomic diffusivity using atomistic simulation data and machine learning.

## Overview

The pipeline ingests raw crystallographic structures (POSCAR/CIF) from materials databases, extracts geometric descriptors of grain boundaries, trains a gradient-boosted tree model (XGBoost) to predict diffusivity, and performs statistical validation and interpretability analysis.

## Data Schema

### Raw Data (`data/raw/`)
Raw files downloaded from external sources:
- **Format**: POSCAR or CIF files
- **Metadata**: Stored in `data/metadata.yaml` containing:
 - `source`: Materials Project, OpenKIM, or NIST
 - `version`: Dataset version tag
 - `checksum`: SHA-256 hash of the file
 - `retrieval_date`: ISO 8601 timestamp

### Parsed Geometry (`data/processed/parsed_geometry.parquet`)
Intermediate dataset containing extracted geometric features:
- `structure_id`: Unique identifier
- `misorientation_angle`: Float (degrees)
- `sigma_value`: Integer (Σ value from CSL)
- `boundary_plane_normal_h`, `boundary_plane_normal_k`, `boundary_plane_normal_l`: Miller indices
- `rodrigues_x`, `rodrigues_y`, `rodrigues_z`: Rodrigues vector components
- `boundary_width`: Float (Å)
- `excess_volume`: Float (Å³)
- `temperature`: Float (K)
- `composition`: String (chemical formula)
- `diffusivity`: Float (m²/s)
- `simulation_method`: String (DFT, MD, KMC)
- `potential_id`: String (interatomic potential identifier)

### Cleaned Dataset (`data/processed/cleaned_dataset.parquet`)
Final dataset after filtering missing values and enforcing minimum record count (n ≥ 500):
- Same schema as parsed geometry with additional validation flags
- Missing required features result in record exclusion

### Model Artifacts (`models/`)
- `best_model.json`: Trained XGBoost model parameters and metadata

### Reports (`artifacts/reports/`)
- `collinearity_diagnostic.json`: Mutual Information analysis between misorientation and Σ value
- `training_metrics.json`: R², RMSE, MAPE on test set
- `validation_report.json`: Cross-validation metrics and bias test results

### Figures (`artifacts/figures/`)
- SHAP summary plots and sensitivity analysis tables

## API Usage

### Download Module (`code/download.py`)
Fetches raw structures from external APIs.

```python
from download import fetch_materials_project_data, fetch_openkim_data, save_raw_data

# Fetch from Materials Project
mp_data = fetch_materials_project_data(
 keywords=["grain boundary", "bicrystal"],
 properties=["diffusivity"]
)

# Fetch from OpenKIM
kim_data = fetch_openkim_data(
 keywords=["grain boundary"]
)

# Save raw files with checksums
save_raw_data(mp_data, kim_data, output_dir="data/raw/")
```

**Requirements**:
- `MP_API_KEY` environment variable (Materials Project)
- `OPENKIM_API_KEY` environment variable (OpenKIM)

### Geometry Parser (`code/geometry_parser.py`)
Parses crystallographic files and extracts grain boundary descriptors.

```python
from geometry_parser import parse_structure_file, extract_geometry_features

# Parse a single structure file
structure = parse_structure_file("data/raw/structure_001.cif")

# Extract all features
features = extract_geometry_features(structure)
# Returns: {
# 'misorientation_angle': float,
# 'sigma_value': int,
# 'boundary_plane_normal': (h, k, l),
# 'rodrigues_vector': (x, y, z),
# 'boundary_width': float,
# 'excess_volume': float
# }
```

### Preprocessing (`code/preprocess.py`)
Validates features and enforces data sufficiency constraints.

```python
from preprocess import load_parsed_data, validate_features, enforce_minimum_records

# Load parsed geometry
df = load_parsed_data("data/processed/parsed_geometry.parquet")

# Validate required features
valid_df, missing = validate_features(df, required_features=[
 'misorientation_angle', 'sigma_value', 'boundary_plane_normal',
 'temperature', 'composition', 'diffusivity'
])

# Enforce minimum record count (n >= 500)
final_df = enforce_minimum_records(valid_df, min_records=500)
```

### Training (`code/train.py`)
Trains XGBoost model with hyperparameter tuning.

```python
from train import load_and_prepare_data, tune_hyperparameters, evaluate_model

# Load and split data
X_train, X_val, X_test, y_train, y_val, y_test = load_and_prepare_data(
 "data/processed/cleaned_dataset.parquet",
 target='diffusivity',
 test_size=0.15,
 val_size=0.15
)

# Hyperparameter tuning
best_model, best_params = tune_hyperparameters(
 X_train, y_train, X_val, y_val,
 param_grid={
 'max_depth': [3, 10],
 'learning_rate': [0.01, 0.3],
 'n_estimators': [50, 300]
 }
)

# Evaluate on test set
metrics = evaluate_model(best_model, X_test, y_test)
# Returns: {'r2': float, 'rmse': float, 'mape': float}
```

### Diagnostics (`code/diagnostics.py`)
Computes mutual information for feature dependency analysis.

```python
from diagnostics import compute_mutual_information, run_collinearity_diagnostic

# Calculate MI between misorientation and Σ value
mi_score = compute_mutual_information(
 misorientation_angles, sigma_values
)

# Run full collinearity diagnostic
report = run_collinearity_diagnostic("data/processed/cleaned_dataset.parquet")
```

### Validation (`code/validate.py`)
Performs cross-validation and bias testing.

```python
from validate import perform_cross_validation, run_regression_bias_test

# 5-fold cross-validation
cv_results = perform_cross_validation(model, X, y, n_folds=5)

# Regression bias test with Bonferroni correction
bias_test = run_regression_bias_test(y_true, y_pred, alpha=0.017)
```

### Interpretability (`code/interpret.py`)
Generates SHAP analysis and sensitivity tables.

```python
from interpret import generate_shap_analysis, perform_sensitivity_analysis

# SHAP feature importance
shap_results = generate_shap_analysis(model, X_test)

# Sensitivity analysis across R² thresholds
sensitivity_table = perform_sensitivity_analysis(
 model, X_test, y_test,
 thresholds=[0.5, 0.6, 0.7, 0.8, 0.9]
)
```

## Execution Pipeline

The pipeline executes in the following order:

1. **T009**: `python code/download.py` - Fetch raw data
2. **T010**: `python code/geometry_parser.py` - Parse structures
3. **T011**: `python code/preprocess.py` - Clean and validate
4. **T016**: `python code/diagnostics.py` - Collinearity check
5. **T012**: `python code/train.py` - Train model
6. **T017**: `python code/validate.py` - Validate model
7. **T021**: `python code/interpret.py` - Interpret results

## Dependencies

See `requirements.txt` for pinned versions:
- pandas
- numpy
- scikit-learn
- xgboost
- shap
- matplotlib
- requests
- pymatgen
- python-dotenv

## Environment Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # or venv\Scripts\activate # Windows
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure API keys in `.env`:
 ```
 MP_API_KEY=your_materials_project_key
 OPENKIM_API_KEY=your_openkim_key
 ```

4. Run the pipeline:
 ```bash
 python code/download.py
 python code/geometry_parser.py
 python code/preprocess.py
 python code/diagnostics.py
 python code/train.py
 python code/validate.py
 python code/interpret.py
 ```

## Output Verification

After successful execution, verify these artifacts exist:
- `data/raw/` - Raw structure files with checksums
- `data/processed/parsed_geometry.parquet` - Parsed geometry
- `data/processed/cleaned_dataset.parquet` - Cleaned dataset (n ≥ 500)
- `models/best_model.json` - Trained model
- `artifacts/reports/training_metrics.json` - Training metrics
- `artifacts/reports/validation_report.json` - Validation report
- `artifacts/figures/shap_summary.png` - SHAP plot
- `artifacts/reports/threshold-variation-table.csv` - Sensitivity table

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

Run quickstart validation:
```bash
python code/validate_quickstart.py
```
