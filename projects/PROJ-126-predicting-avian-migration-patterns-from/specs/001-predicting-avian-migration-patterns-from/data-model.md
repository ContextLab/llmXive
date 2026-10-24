# Data Model: Predicting Avian Migration Patterns

## Entity‑Relationship Overview
The pipeline centers on a single canonical entity – **GridCellObservation** – which aggregates citizen‑science bird records and remote‑sensing covariates into a spatiotemporal grid cell. All downstream artifacts (model inputs, metrics, visualizations) derive from this entity, satisfying the Single Source of Truth principle.

### Core Entities

| Entity | Source | Key Attributes |
|--------|--------|----------------|
| **RawChecklist** | eBird Basic Dataset (CSV) | `checklist_id`, `date`, `latitude`, `longitude`, `species_code`, `obs_count`, `duration_min`, `distance_km`, `num_observers` |
| **GridCellObservation** | Aggregated `RawChecklist` + MODIS rasters | `grid_cell_id`, `year`, `week_number`, `total_obs_count`, `cumulative_count`, `first_arrival_week`, `threshold_used`, `effort_covariate`, `data_quality_flag`, `lst_lag_1‑4`, `ndvi_lag_1‑4`, `residual_first_arrival` |
| **ModelPrediction** | XGBoost + GP output | `grid_cell_id`, `year`, `week_number`, `predicted_arrival_day_of_year`, `actual_arrival_day_of_year`, `residual`, `shap_lst`, `shap_ndvi` |
| **ModelPerformanceMetric** | Statistical tests | `model_name`, `metric_type`, `value`, `p_value`, `confidence_interval_lower`, `confidence_interval_upper`, `threshold_sweep`, `feasibility` |
| **SpatialRandomEffect** | GP residual correction | `cell_id`, `gp_predicted_residual` |

## Data Flow Diagram
1. **Ingestion** (`data_loader.py`) → `RawChecklist` CSV (`data/raw/ebd_subset.csv`).  
2. **Filtering** (complete‑checklist criteria) → retained rows.  
3. **Spatial Binning** → `GridCellObservation` rows (`data/processed/first_arrival_sweep.csv`).  
4. **Environmental Enrichment** (MODIS resampling) → lagged temperature/NDVI fields attached.  
5. **Effort‑Covariate**: stored as `effort_covariate` (predictor only for secondary model); **not** used in target definition.  
6. **Primary Target**: `first_arrival_week` derived from **raw** cumulative‑count threshold (no scaling).  
7. **Model training** (`model_training.py`) → `ModelPrediction` (`data/outputs/predictions.csv`).  
8. **GP Spatial Correction** → `residual_first_arrival` added to `GridCellObservation`.  
9. **Evaluation** (`evaluation.py`) → `ModelPerformanceMetric` (`data/processed/metrics.json`).  
10. **Visualization** (`visualization.py`) → PNG maps (`data/outputs/`).  

All **CSV**/JSON artifacts are validated against the JSON‑Schema contracts in `contracts/`.

## Data Constraints & Validation Rules
- **Grid Resolution**: Fixed at 0.5° × 0.5° (enforced in `preprocessing.py`).  
- **Temporal Range**: 2015 – 2022 inclusive (validated during loading).  
- **Species**: Only `species_code == "SRUT"` (Redstart).  
- **Observation Minimum**: Exclude **any** grid cell **with <10** total annual observations (FR‑003).  
- **Effort covariate**: `effort_covariate` is **included only as a predictor** in the secondary model (FR‑008); it is **not** part of the target definition, avoiding circularity.  
- **First‑Arrival Threshold**: Raw cumulative count; thresholds {3, 5, 10} recorded in `threshold_used`. If never reached, `first_arrival_week` = `null` and `data_quality_flag="undetermined"`.  
- **Environmental Coverage**: MODIS pixels covering ≥ 95 % of grid cells each week; validated against GHCN stations (FR‑011). Cells failing are excluded from modeling.  
- **Spatial Random‑Effect**: Gaussian Process fitted to XGBoost residuals (FR‑010).  
- **Residual First Arrival**: After GP correction, the residualized target is stored as `residual_first_arrival` (numeric, may be null).  
- **Schema Compliance**: Every output file must validate against its respective contract (`grid_cell_observation.schema.yaml`, `metrics.schema.yaml`). Validation is performed against **both** `dataset.schema.yaml` **and** `dataset_schema.schema.yaml` for the processed CSV.

## Mapping to Contracts
- **`grid_cell_observation.schema.yaml`** defines the exact column names, types, required fields, and allowed enum values for `first_arrival_sweep.csv`.  
- **`metrics.schema.yaml`** defines the JSON structure stored in `metrics.json`, now including the `spatial_bootstrap_p` and `residual_first_arrival` fields.  
- **`model_metrics.schema.yaml`** and **`model_output_schema.schema.yaml`** are used in Phase 2 to validate model‑level outputs (see `plan.md`).  
- **`output.schema.yaml`** is validated against the final predictions file in Phase 2 (see `plan.md`).  
