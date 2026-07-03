# Data Schema Documentation

This document describes the data schemas used throughout the pipeline.

## 1. Raw Data (`data/raw/`)

Raw data is downloaded from external APIs and stored in JSON format.

### Schema: `mp_gb_data.json`

```json
{
 "source": "Materials Project",
 "version": "v2",
 "retrieved_at": "2023-10-27T10:00:00Z",
 "records": [
 {
 "material_id": "mp-12345",
 "structure_file": "data/raw/mp-12345_POSCAR",
 "properties": {
 "diffusivity": 1.2e-10,
 "temperature": 1000.0,
 "composition": ["Fe", "Cr"]
 },
 "metadata": {
 "simulation_method": "DFT",
 "potential_id": "KIM-12345"
 }
 }
 ]
}
```

### Validation Rules
- `material_id`: Must be non-empty string.
- `structure_file`: Must exist on disk.
- `diffusivity`: Must be positive float.
- `temperature`: Must be positive float.

---

## 2. Parsed Geometry (`data/processed/parsed_geometry.parquet`)

Intermediate data after parsing structure files.

### Columns

| Column | Type | Description |
|---------------------|---------|--------------------------------------|
| material_id | string | Unique identifier |
| misorientation_angle| float | Angle in degrees |
| boundary_plane_hkl | string | Miller indices (h,k,l) |
| rodrigues_vector | string | Rodrigues vector (x,y,z) |
| boundary_width | float | Width in Angstroms |
| excess_volume | float | Excess volume per area |
| sigma_value | int | CSL Σ value |
| temperature | float | Simulation temperature |
| diffusivity | float | Target variable |
| simulation_method | string | DFT, MD, KMC |
| potential_id | string | Potential identifier |

---

## 3. Cleaned Dataset (`data/processed/cleaned_dataset.parquet`)

Final dataset after filtering and tagging.

### Schema

Same as `parsed_geometry.parquet` but with:
- Removed records with missing required features.
- Added `data_quality_flag` column (if applicable).

### Required Features
- `misorientation_angle`
- `sigma_value`
- `boundary_plane_hkl`
- `temperature`
- `diffusivity`
- `boundary_width`
- `excess_volume`

If fewer than 500 records remain after filtering, the pipeline halts with `DataInsufficiencyError`.

---

## 4. Model Artifact (`models/best_model.json`)

Trained XGBoost model and metadata.

### Schema

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
 "boundary_plane_hkl": 0.15,
 "temperature": 0.12,
 "boundary_width": 0.10,
 "excess_volume": 0.08,
 "simulation_method": 0.07,
 "potential_id": 0.05
 },
 "created_at": "2023-10-27T10:00:00Z",
 "data_checksum": "abc123..."
}
```

---

## 5. Diagnostic Report (`artifacts/reports/collinearity_diagnostic.json`)

Mutual Information and collinearity diagnostics.

### Schema

```json
{
 "mutual_information": {
 "misorientation_angle_vs_sigma": 0.85
 },
 "warning": "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal. [UNRESOLVED-CLAIM: c_b8d1008b — status=not_enough_info]",
 "timestamp": "2023-10-27T10:00:00Z"
}
```

---

## 6. Validation Report (`artifacts/reports/validation_report.json`)

Cross-validation and bias test results.

### Schema

```json
{
 "cross_validation": {
 "k_folds": 5,
 "r2_mean": 0.81,
 "r2_std": 0.03,
 "rmse_mean": 0.055,
 "mape_mean": 0.13
 },
 "bias_test": {
 "intercept": 0.02,
 "slope": 0.98,
 "p_value": 0.15,
 "bonferroni_adjusted_p": 0.45
 },
 "threshold_check": {
 "r2_std_threshold": 0.05,
 "passed": true
 }
}
```

---

## 7. Sensitivity Table (`artifacts/reports/threshold-variation-table.csv`)

Pass rates for different R² thresholds.

### Schema

```csv
threshold,pass_rate,justification
0.6,0.95,Community standard for materials property prediction
0.7,0.82,Primary target threshold
0.8,0.55,High performance target
```

---

## Data Provenance (`data/metadata.yaml`)

Tracks data source, version, and checksum.

```yaml
- source: Materials Project
 version: v2
 retrieval_date: 2023-10-27
 checksum: abc123...
 record_count: 550
- source: OpenKIM
 version: 2023.10
 retrieval_date: 2023-10-27
 checksum: def456...
 record_count: 200
```