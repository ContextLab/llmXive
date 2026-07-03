# Data Schema Documentation

This document defines the data structures used throughout the pipeline.

## Raw Data Metadata (`data/metadata.yaml`)

Tracks provenance for all downloaded data.

```yaml
source: <string> # e.g., "materials_project", "openkim", "nist"
version: <string> # Version tag of the dataset
checksum: <string> # SHA-256 hash of the raw data
retrieval_date: <ISO8601> # Date and time of retrieval
```

## Parsed Geometry (`data/processed/parsed_geometry.parquet`)

Columns:

- `structure_id`: str (unique identifier)
- `misorientation_angle`: float (degrees)
- `sigma_value`: int (CSL Σ value)
- `boundary_plane_normal`: list of 3 floats (normalized vector)
- `miller_indices`: list of 3 ints (h, k, l)
- `rodrigues_vector`: list of 3 floats
- `boundary_width`: float (Å)
- `excess_volume`: float (Å³)
- `temperature`: float (K)
- `composition`: str (e.g., "Cu")
- `diffusivity`: float (m²/s)
- `simulation_method`: str ("DFT", "MD", "KMC")
- `potential_id`: str

## Cleaned Dataset (`data/processed/cleaned_dataset.parquet`)

Subset of parsed geometry with:
- No missing values in required features.
- Minimum 500 records.
- Additional tags for metadata features.

## Model Artifacts (`models/best_model.json`)

JSON serialization of the trained XGBoost model, including:
- Hyperparameters (`max_depth`, `learning_rate`, `n_estimators`, etc.)
- Feature names
- Trained tree structure

## Reports

### `artifacts/reports/collinearity_diagnostic.json`

```json
{
 "mutual_information": <float>,
 "warning": "<string>"
}
```

### `artifacts/reports/training_metrics.json`

```json
{
 "r2": <float>,
 "rmse": <float>,
 "mape": <float>
}
```

### `artifacts/reports/validation_report.json`

```json
{
 "cv_r2_mean": <float>,
 "cv_r2_std": <float>,
 "bias_intercept": <float>,
 "bias_slope": <float>,
 "bias_p_value": <float>,
 "bonferroni_corrected": true
}
```

### `artifacts/reports/threshold-variation-table.csv`

CSV with columns:
- `threshold`: float
- `pass_rate`: float (proportion of folds passing)
