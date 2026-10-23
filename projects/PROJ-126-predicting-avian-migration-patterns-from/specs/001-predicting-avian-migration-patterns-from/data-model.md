# Data Model: Predicting Avian Migration Patterns

## Entity‑Relationship Overview
The pipeline revolves around a single canonical entity – **GridCellObservation** – which aggregates citizen‑science bird records and remote‑sensing covariates into a spatiotemporal grid cell. All downstream artifacts (model inputs, metrics, visualizations) derive from this entity, satisfying the Single Source of Truth principle.

### Core Entities

| Entity | Source | Key Attributes |
|--------|--------|----------------|
| **RawChecklist** | eBird Basic Dataset (CSV) | `checklist_id`, `date`, `latitude`, `longitude`, `species_code`, `obs_count`, `duration_min`, `distance_km`, `num_observers` |
| **GridCellObservation** | Aggregated `RawChecklist` + MODIS rasters | `grid_cell_id`, `year`, `week_number`, `total_obs_count`, `cumulative_count`, `first_arrival_week`, `lst_lag_1‑4`, `ndvi_lag_1‑4`, `effort_covariate`, `data_quality_flag`, `threshold_used` |
| **ModelPrediction** | XGBoost + spline output | `grid_cell_id`, `year`, `week_number`, `predicted_arrival_day_of_year`, `actual_arrival_day_of_year`, `residual`, `shap_lst`, `shap_ndvi` |
| **ModelPerformanceMetric** | Statistical tests | `model_name`, `metric_type`, `value`, `p_value`, `confidence_interval_lower`, `confidence_interval_upper`, `threshold_sweep`, `feasibility` |

## Data Flow Diagram
1. **Ingestion** (`data_loader.py`) → `RawChecklist` CSV (`data/raw/ebd_subset.csv`).  
2. **Filtering** (complete‑checklist criteria) → retained rows.  
3. **Spatial Binning** → `GridCellObservation` rows (`data/processed/first_arrival_sweep.csv`).  
4. **Environmental Enrichment** (MODIS resampling) → lagged temperature/NDVI fields attached.  
5. **Model Training** (`model_training.py`) → `ModelPrediction` (`data/outputs/predictions.csv`).  
6. **Evaluation** (`evaluation.py`) → `ModelPerformanceMetric` (`data/processed/metrics.json`).  
7. **Visualization** (`visualization.py`) → PNG maps (`data/outputs/`).  

All CSV/JSON artifacts are validated against the JSON‑Schema contracts in `contracts/`.

## Data Constraints & Validation Rules
- **Grid Resolution**: Fixed at 0.5° × 0.5° (enforced in `preprocessing.py`).  
- **Temporal Range**: 2015 – 2022 inclusive (validated during loading).  
- **Species Filter**: Only `species_code == "SRUT"` (Redstart).  
- **Observation Minimum**: Exclude cells with `<10` total annual observations (FR‑003).  
- **Effort Covariate**: `effort_covariate` is **included only as a predictor**; it is **not** used to adjust the first‑arrival threshold (addresses scientific‑soundness and methodology‑4917fa04).  
- **First‑Arrival Threshold**: Raw cumulative count threshold *k* ∈ {3, 5, 10}. If the threshold is never reached, `first_arrival_week` is set to `null` and flagged `data_quality_flag="undetermined"`.  
- **Environmental Coverage**: MODIS pixels covering ≥ 95 % of the study domain; cells failing this receive `data_quality_flag="missing_env"` and are omitted from modeling (FR‑011).  
- **Schema Compliance**: Every output file must validate against its respective contract (`grid_cell_observation.schema.yaml`, `metrics.schema.yaml`). Validation is performed against **both** `dataset.schema.yaml` and `dataset_schema.schema.yaml` for the processed CSV.

## Mapping to Contracts
- **`grid_cell_observation.schema.yaml`** defines the exact column names, types, required fields, and allowed enum values for `first_arrival_sweep.csv`.  
- **`metrics.schema.yaml`** defines the JSON structure stored in `metrics.json`, including the newly added `spatial_bootstrap_p` field.  
- **`model_metrics.schema.yaml`** and **`model_output_schema.schema.yaml`** will be used in Phase 2 to validate model‑level outputs (see plan.md).  

---

