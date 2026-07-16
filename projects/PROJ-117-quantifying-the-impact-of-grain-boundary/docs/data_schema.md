# Data Schema Documentation

This document describes the data schemas used throughout the grain boundary diffusivity project.

## GrainBoundaryRecord Schema

The `GrainBoundaryRecord` dataclass (defined in `code/models/grain_boundary_record.py`) is the primary data structure for representing grain boundary data.

### Fields

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `material_id` | `str` | Unique identifier for the material from source database | "mp-12345" |
| `misorientation_angle` | `float` | Angle of misorientation between grains in degrees | 36.87 |
| `sigma_value` | `int` | Coincidence Site Lattice (Σ) value | 5 |
| `boundary_plane_normal` | `List[int]` | Miller indices (hkl) of the boundary plane | [1, 0, 0] |
| `rodrigues_vector` | `List[float]` | Rodrigues vector representation of misorientation | [0.1, 0.2, 0.3] |
| `boundary_width` | `float` | Width of the grain boundary in Angstroms | 12.5 |
| `excess_volume` | `float` | Excess volume at the boundary in Å³/atom | 0.05 |
| `temperature` | `float` | Temperature in Kelvin | 1000.0 |
| `composition` | `str` | Chemical composition string | "Al" |
| `diffusivity` | `float` | Atomic diffusivity (target variable) in m²/s | 1.2e-12 |
| `simulation_method` | `str` | Method used for simulation | "MD" |
| `potential_id` | `str` | Interatomic potential identifier | "EAM_Al_2020" |
| `source` | `str` | Data source | "Materials Project" |
| `checksum` | `str` | SHA-256 checksum of the raw file | "a1b2c3d4..." |
| `retrieval_date` | `str` | Date of data retrieval (ISO format) | "2024-01-15" |

### JSON Representation

```json
{
 "material_id": "mp-12345",
 "misorientation_angle": 36.87,
 "sigma_value": 5,
 "boundary_plane_normal": [1, 0, 0],
 "rodrigues_vector": [0.1, 0.2, 0.3],
 "boundary_width": 12.5,
 "excess_volume": 0.05,
 "temperature": 1000.0,
 "composition": "Al",
 "diffusivity": 1.2e-12,
 "simulation_method": "MD",
 "potential_id": "EAM_Al_2020",
 "source": "Materials Project",
 "checksum": "a1b2c3d4e5f6...",
 "retrieval_date": "2024-01-15"
}
```

## Metadata Schema

The `data/metadata.yaml` file tracks data provenance and retrieval information.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `source` | `str` | Name of the data source (Materials Project, OpenKIM, NIST) |
| `version_tag` | `str` | Version tag for the dataset |
| `checksum` | `str` | SHA-256 checksum of the raw data bundle |
| `retrieval_date` | `str` | Date of data retrieval (ISO format) |
| `record_count` | `int` | Number of records in the dataset |
| `file_paths` | `List[str]` | List of paths to raw data files |

### Example

```yaml
source: Materials Project
version_tag: v1.0.0
checksum: "a1b2c3d4e5f67890..."
retrieval_date: "2024-01-15"
record_count: 523 [UNRESOLVED-CLAIM: c_6e4764e8 — status=not_enough_info]
file_paths:
 - "data/raw/mp_grain_boundaries/POSCAR_001"
 - "data/raw/mp_grain_boundaries/POSCAR_002"
```

## Processed Data Formats

### Parsed Geometry (`data/processed/parsed_geometry.parquet`)

Parquet file containing intermediate geometry features extracted from raw structures.

**Columns:**
- `material_id` (str)
- `misorientation_angle` (float)
- `sigma_value` (int)
- `boundary_plane_normal` (object, list of ints)
- `rodrigues_vector` (object, list of floats)
- `boundary_width` (float)
- `excess_volume` (float)
- `source_file` (str)
- `checksum` (str)

### Cleaned Dataset (`data/processed/cleaned_dataset.parquet`)

Parquet file containing the final cleaned dataset ready for modeling.

**Columns:**
- All columns from `parsed_geometry.parquet`
- `temperature` (float)
- `composition` (str)
- `diffusivity` (float)
- `simulation_method` (str, tagged)
- `potential_id` (str, tagged)
- `retrieval_date` (str)

## Output Artifacts

### Training Metrics (`artifacts/reports/training_metrics.json`)

```json
{
 "r2": 0.85,
 "rmse": 0.12,
 "mape": 15.3,
 "test_size": 75,
 "training_date": "2024-01-15T10:30:00"
}
```

### Validation Report (`artifacts/reports/validation_report.json`)

```json
{
 "cross_validation": {
 "r2_mean": 0.84,
 "r2_std": 0.03,
 "rmse_mean": 0.13,
 "mape_mean": 16.1,
 "k_folds": 5
 },
 "bias_test": {
 "intercept": 0.02,
 "slope": 0.98,
 "p_value_intercept": 0.15,
 "p_value_slope": 0.22,
 "alpha_adjusted": 0.017
 },
 "bias_assessment": "No significant bias detected"
}
```

### Collinearity Diagnostic (`artifacts/reports/collinearity_diagnostic.json`)

```json
{
 "mutual_information": {
 "misorientation_angle_vs_sigma": 0.85,
 "warning": "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
 },
 "timestamp": "2024-01-15T10:00:00"
}
```

### Threshold Sensitivity Table (`artifacts/reports/threshold-variation-table.csv`)

| threshold | pass_rate | fold_count | total_folds |
|-----------|-----------|------------|-------------|
| 0.5 | 1.0 | 5 | 5 |
| 0.6 | 1.0 | 5 | 5 |
| 0.7 | 0.8 | 4 | 5 |
| 0.8 | 0.4 | 2 | 5 |
| 0.9 | 0.0 | 0 | 5 |

## Data Flow

1. **Raw Data** (`data/raw/`) - Downloaded POSAR/CIF files from external APIs
2. **Parsed Geometry** (`data/processed/parsed_geometry.parquet`) - Extracted geometric features
3. **Cleaned Dataset** (`data/processed/cleaned_dataset.parquet`) - Validated and filtered records
4. **Model Artifacts** (`models/`) - Trained XGBoost models
5. **Reports** (`artifacts/reports/`) - Diagnostic and validation reports
6. **Figures** (`artifacts/figures/`) - SHAP plots and visualizations
