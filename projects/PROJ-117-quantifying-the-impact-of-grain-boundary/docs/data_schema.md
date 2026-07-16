# Data Schema Documentation

This document describes the data schemas used throughout the Grain Boundary Diffusivity pipeline.

## Raw Data Schema

### Source: Materials Project

**Endpoint**: `

**Response Fields**:
```json
{
 "task_id": "string",
 "material_id": "string",
 "structure": {
 "sites": [{"species": [{"element": "string", "occu": float}], "xyz": [float, float, float]}],
 "lattice": {"a": float, "b": float, "c": float, "alpha": float, "beta": float, "gamma": float}
 },
 "properties": {
 "diffusivity": float,
 "temperature": float
 },
 "metadata": {
 "simulation_method": "string",
 "potential_id": "string"
 }
}
```

### Source: OpenKIM

**Endpoint**: ` Name or service not known)"))]

**Response Fields**:
```json
{
 "id": "string",
 "structure_file": "base64_encoded_poscar_or_cif",
 "properties": {
 "diffusivity": float,
 "temperature": float
 },
 "metadata": {
 "simulation_method": "string",
 "potential_id": "string"
 }
}
```

## Processed Data Schema

### Parsed Geometry (`data/processed/parsed_geometry.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `structure_id` | string | Unique identifier |
| `source` | string | Data source (Materials Project, OpenKIM, NIST) |
| `misorientation_angle` | float | Angle in degrees [0, 90] |
| `sigma_value` | int | Σ value from CSL (odd integer) |
| `boundary_plane_normal_h` | int | Miller index h |
| `boundary_plane_normal_k` | int | Miller index k |
| `boundary_plane_normal_l` | int | Miller index l |
| `rodrigues_x` | float | Rodrigues vector x component |
| `rodrigues_y` | float | Rodrigues vector y component |
| `rodrigues_z` | float | Rodrigues vector z component |
| `boundary_width` | float | Boundary width in Å |
| `excess_volume` | float | Excess volume in Å³ |
| `temperature` | float | Temperature in K |
| `composition` | string | Chemical formula |
| `diffusivity` | float | Atomic diffusivity in m²/s |
| `simulation_method` | string | DFT, MD, or KMC |
| `potential_id` | string | Interatomic potential identifier |

### Cleaned Dataset (`data/processed/cleaned_dataset.parquet`)

Same schema as parsed geometry with additional validation:
- No null values in required columns
- `n >= 500` records
- Metadata features tagged for encoding

## Output Artifacts Schema

### `artifacts/reports/collinearity_diagnostic.json`

```json
{
 "mutual_information": {
 "misorientation_vs_sigma": 0.45,
 "misorientation_vs_plane_normal": 0.12,
 "sigma_vs_plane_normal": 0.08
 },
 "warnings": ["MI > 0.8 indicates strong dependency"],
 "timestamp": "2024-01-15T10:30:00Z"
}
```

### `artifacts/reports/training_metrics.json`

```json
{
 "r2": 0.78,
 "rmse": 0.15,
 "mape": 12.3,
 "test_size": 150,
 "hyperparameters": {
 "max_depth": 7,
 "learning_rate": 0.1,
 "n_estimators": 200
 },
 "timestamp": "2024-01-15T11:00:00Z"
}
```

### `artifacts/reports/validation_report.json`

```json
{
 "cross_validation": {
 "r2_mean": 0.76,
 "r2_std": 0.03,
 "rmse_mean": 0.16,
 "mape_mean": 13.1
 },
 "bias_test": {
 "intercept": 0.02,
 "slope": 0.98,
 "intercept_pvalue": 0.45,
 "slope_pvalue": 0.01
 },
 "bonferroni_alpha": 0.017,
 "timestamp": "2024-01-15T12:00:00Z"
}
```

### `artifacts/reports/threshold-variation-table.csv`

| threshold | pass_rate | fold_count |
|-----------|-----------|------------|
| 0.50 | 1.00 | 5 |
| 0.60 | 1.00 | 5 |
| 0.70 | 0.80 | 4 |
| 0.80 | 0.40 | 2 |
| 0.90 | 0.00 | 0 |

## Metadata Schema (`data/metadata.yaml`)

```yaml
version: "1.0"
datasets:
 - source: "Materials Project"
 version_tag: "2024.01"
 checksum: "sha256:abc123..."
 retrieval_date: "2024-01-15T09:00:00Z"
 record_count: 350
 - source: "OpenKIM"
 version_tag: "2024.01"
 checksum: "sha256:def456..."
 retrieval_date: "2024-01-15T09:30:00Z"
 record_count: 200
```

## Data Constraints

### Required Features
The following features are required for model training:
- `misorientation_angle`
- `sigma_value`
- `boundary_plane_normal` (h, k, l)
- `temperature`
- `composition`
- `diffusivity`
- `boundary_width`
- `excess_volume`

### Minimum Record Count
- **Constraint**: `n >= 500` valid records
- **Error**: If violated, pipeline exits with code 1 and logs:
 `"Data Insufficiency: {valid_count} < 500. Missing features: {missing_feature_list}"`

### Data Types
- Floats: 64-bit precision
- Integers: 32-bit for indices, 64-bit for Σ value
- Strings: UTF-8 encoding
- Dates: ISO 8601 format
