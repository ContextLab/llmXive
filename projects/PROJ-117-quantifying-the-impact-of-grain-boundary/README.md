# Quantifying the Impact of Grain Boundary Character on Diffusivity

This project implements an automated science pipeline to quantify how grain boundary character (misorientation, boundary plane, Σ value) influences atomic diffusivity in materials.

## Project Structure

```
.
├── code/ # Source code modules
│ ├── config/ # Configuration utilities
│ ├── models/ # Data models (e.g., GrainBoundaryRecord)
│ ├── utils.py # Shared utilities (checksums, logging)
│ ├── diagnostics.py # Collinearity and MI diagnostics
│ ├── download.py # Data retrieval from external APIs
│ ├── geometry_parser.py # Structure parsing and feature extraction
│ ├── preprocess.py # Data cleaning and feature engineering
│ ├── train.py # Model training and hyperparameter tuning
│ ├── validate.py # Cross-validation and bias testing
│ └── interpret.py # SHAP analysis and sensitivity testing
├── data/
│ ├── raw/ # Downloaded raw data (POSCAR, CIF, JSON)
│ ├── processed/ # Cleaned and parsed datasets
│ └── metadata.yaml # Provenance tracking
├── models/ # Trained model artifacts (JSON)
├── artifacts/
│ ├── figures/ # SHAP plots, sensitivity tables
│ └── reports/ # Diagnostics, validation, training metrics
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## API Usage

### External Data Sources

The pipeline retrieves data from the following APIs:

- **Materials Project**: Requires `MP_API_KEY` environment variable.
 - Endpoint: `
 - Used for: Crystal structures, grain boundary configurations, diffusivity data.
 - Authentication: Bearer token via `X-API-Key` header.

- **OpenKIM**: Requires `KIM_API_KEY` environment variable.
 - Endpoint: `
 - Used for: Interatomic potentials and simulation results.

- **NIST**: Public repository for materials data.
 - Used for: Validation datasets and benchmark structures.

### Usage Example: Data Download

```python
from code.download import fetch_materials_project_data, save_raw_data

# Fetch grain boundary data
data = fetch_materials_project_data(
 keywords=["grain boundary", "bicrystal"],
 properties=["diffusivity"]
)
save_raw_data(data, "data/raw/mp_gb_data.json")
```

### Usage Example: Geometry Parsing

```python
from code.geometry_parser import parse_structure_file, calculate_sigma_value

# Parse a POSAR file
structure = parse_structure_file("data/raw/example_POSCAR")
sigma = calculate_sigma_value(misorientation_angle=38.9)
miller_indices = calculate_miller_indices(normal_vector=[1, 0, 0], lattice=structure.lattice)
```

### Usage Example: Model Training

```python
from code.train import main as train_main

# Run full training pipeline
train_main()
# Outputs: models/best_model.json, artifacts/reports/training_metrics.json
```

## Data Schema

### Raw Data Schema (`data/raw/*.json`)

```yaml
source: <string> # e.g., "Materials Project"
version: <string> # API version or dataset version
retrieved_at: <ISO8601>
records:
 - material_id: <string>
 structure_file: <string> # Path to POSAR/CIF
 properties:
 diffusivity: <float>
 temperature: <float>
 composition: <list>
 metadata:
 simulation_method: <string> # DFT, MD, KMC
 potential_id: <string>
```

### Processed Dataset Schema (`data/processed/cleaned_dataset.parquet`)

| Column Name | Type | Description |
|---------------------|---------|----------------------------------------------|
| material_id | string | Unique identifier from source |
| misorientation_angle| float | Angle in degrees |
| sigma_value | int | Coincidence Site Lattice Σ value |
| boundary_plane_hkl | string | Miller indices (hkl) as "h,k,l" |
| rodrigues_vector | string | Rodrigues vector components "x,y,z" |
| boundary_width | float | Width in Angstroms |
| excess_volume | float | Excess volume per area |
| temperature | float | Simulation temperature (K) |
| diffusivity | float | Target variable (atomic diffusivity) |
| simulation_method | string | Categorical: DFT, MD, KMC |
| potential_id | string | Identifier for interatomic potential |

### Model Artifact Schema (`models/best_model.json`)

```json
{
 "model_type": "XGBRegressor",
 "hyperparameters": {
 "max_depth": 6,
 "learning_rate": 0.1,
 "n_estimators": 200
 },
 "training_metrics": {
 "r2": 0.82,
 "rmse": 0.05,
 "mape": 0.12
 },
 "feature_importance": {
 "misorientation_angle": 0.25,
 "sigma_value": 0.18,
...
 },
 "created_at": "2023-10-27T10:00:00Z"
}
```

## Configuration

- **Environment Variables**: Set `MP_API_KEY`, `KIM_API_KEY` in `.env` (not committed).
- **Thresholds**: R² ≥ 0.7 threshold is configured in `code/config/threshold_config.py`.
- **Logging**: Configured via `code/utils.py` with file and console handlers.

## Running the Pipeline

1. Install dependencies: `pip install -r requirements.txt`
2. Set API keys: `export MP_API_KEY=your_key`
3. Run download: `python code/download.py`
4. Run parsing: `python code/geometry_parser.py`
5. Run preprocessing: `python code/preprocess.py`
6. Run diagnostics: `python code/diagnostics.py`
7. Run training: `python code/train.py`
8. Run validation: `python code/validate.py`
9. Run interpretation: `python code/interpret.py`

## Testing

Run unit tests: `pytest tests/unit/`
Run integration tests: `pytest tests/integration/`

## License

MIT License
