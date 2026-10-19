# Data Model: Predicting Avian Migration Patterns

## Entity‑Relationship Overview
The pipeline revolves around a single canonical entity – **GridCellObservation** – which aggregates citizen‑science bird records and remote‑sensing covariates into a spatiotemporal grid cell. All downstream artifacts (model inputs, metrics, visualizations) derive from this entity, satisfying the Single Source of Truth principle.

### Core Entities

| Entity | Source | Key Attributes |
|--------|--------|----------------|
| **RawChecklist** | eBird Basic Dataset (CSV) | `checklist_id`, `date`, `latitude`, `longitude`, `species_code`, `obs_count`, `duration_min`, `distance_km`, `num_observers` |
| **GridCellObservation** | Aggregated `RawChecklist` + MODIS rasters | `grid_cell_id`, `year`, `week_number`, `total_obs_count`, `cumulative_count`, `first_arrival_week`, `lst_lag_1‑4`, `evi_lag_1‑4`, `effort_covariate`, `data_quality_flag`, `threshold_used` |
| **ModelPrediction** | XGBoost output (post‑hoc GP corrected) | `grid_cell_id`, `year`, `week_number`, `predicted_arrival_day_of_year`, `actual_arrival_day_of_year`, `residual`, `shap_lst`, `shap_evi` |
| **ModelPerformanceMetric** | Statistical tests | `model_name`, `metric_type`, `value`, `p_value_dm`, `confidence_interval_lower`, `confidence_interval_upper`, `threshold_sweep`, `feasibility` |

## Data Flow Diagram
1. **Ingestion** (`data_loader.py`) → `RawChecklist` CSV (`data/raw/ebd_subset.csv`).  
2. **Filtering** (complete‑checklist criteria) → retained rows.  
3. **Spatial Binning** → `GridCellObservation` rows (`data/processed/first_arrival_sweep.csv`).  
4. **Environmental Enrichment** (MODIS resampling) → lagged temperature/NDVI fields attached.  
5. **Model Training** (`model_training.py`) → `ModelPrediction` (`data/outputs/predictions.csv`).  
6. **Evaluation** → `ModelPerformanceMetric` (`data/processed/metrics.json`).  
7. **Visualization** (`visualization.py`) → PNG maps (`data/outputs/`).  

All CSV/JSON artifacts are validated against the JSON‑Schema contracts in `contracts/`.

## Data Constraints & Validation Rules
- **Grid Resolution**: Fixed at 0.5° × 0.5° (enforced in `preprocessing.py`).  
- **Temporal Range**: 2015 – 2022 inclusive (validated during loading).  
- **Species Filter**: Only `species_code == "SRUT"` (Redstart).  
- **Observation Minimum**: Exclude cells with `<10` total annual observations (FR‑003).  
- **Effort Offset**: The effort covariate is used **only** to adjust the cumulative‑count threshold (see Phase 1.3); it is **not** included as a predictor in the model (addresses scientific_soundness‑c51f4471).  
- **Environmental Coverage**: MODIS pixels covering ≥ 95 % of the regional study domain; cells failing this receive `data_quality_flag="missing_env"` and are omitted from training (FR‑011).  
- **Schema Compliance**: Every output file must validate against its respective contract (`grid_cell_observation.schema.yaml`, `metrics.schema.yaml`).  

## Mapping to Contracts
- **`grid_cell_observation.schema.yaml`** defines the exact column names, types, required fields, and allowed enum values for `first_arrival_sweep.csv`.  
- **`metrics.schema.yaml`** defines the JSON structure stored in `metrics.json`, including the new `Spatial_Permutation_P` metric type.

---


