# Data Model: Predicting Avian Migration Patterns

## 1. Entity Relationship Overview

The data model consists of three primary stages: **Raw Input**, **Processed Grid**, and **Model Output**.

1.  **Raw Input**: Unprocessed eBird checklists and MODIS raster/CSV data.
2.  **Processed Grid**: Aggregated spatiotemporal units (GridCellObservation) containing derived arrival dates and lagged environmental features.
3.  **Model Output**: Performance metrics, feature importance rankings, and SHAP values.

## 2. Data Entities

### 2.1 Raw eBird Checklist (Source)
*Derived from EBD.*
- **Fields**: `unique_id`, `date`, `latitude`, `longitude`, `species_code`, `observation_count`, `duration_min`, `num_observers`, `distance_km`, `complete_checklist` (bool).
- **Constraints**: Only records with `complete_checklist=True`, `duration_min >= 1`, `num_observers >= 1`, `distance_km <= 10` are ingested.

### 2.2 Raw MODIS Data (Source)
*Derived from verified MODIS dataset.*
- **Fields**: `date`, `latitude`, `longitude`, `lst_mean`, `ndvi_mean`, `cloud_cover_pct`.
- **Constraints**: Data must be aligned to 0.5° grid and weekly frequency.

### 2.2 GridCellObservation (Derived)
*The core unit of analysis.*
- **Primary Key**: `grid_cell_id` (e.g., "45.5_-120.5"), `year`, `week_number`.
- **Attributes**:
  - `total_obs_count`: Total number of Redstart observations in this cell/week.
  - `cumulative_count`: Running total of observations for the year in this cell.
  - `first_arrival_week`: Week number where `cumulative_count` reaches threshold $T$ (3, 5, or 10).
  - `lst_lag_1` to `lst_lag_4`: Mean LST 1-4 weeks prior.
  - `ndvi_lag_1` to `ndvi_lag_4`: Mean NDVI 1-4 weeks prior.
  - `data_quality_flag`: "valid", "missing_env", "insufficient_data".
- **Invariants**:
  - `first_arrival_week` is `null` if `cumulative_count` never reaches $T$.
  - `lst_lag_*` and `ndvi_lag_*` are `null` if environmental data is missing for the lag period.

### 2.3 ModelPerformanceMetric (Output)
- **Fields**: `model_type` (temp/ndvi/combined), `threshold` (3/5/10), `rmse`, `pearson_r`, `dm_p_value`, `comparison_baseline` (naive mean).
- **Invariants**: `dm_p_value` is derived from Diebold-Mariano test against the naive baseline on temporal aggregates.

## 3. Data Flow Diagram

```mermaid
graph TD
    A[EBD Raw CSV/Parquet] -->|Filter: Complete Checklists| B(eBird Filtered Stream)
    C[MODIS Raw CSV] -->|Resample: Weekly/0.5°| D(MODIS Resampled)
    B -->|Aggregate: 0.5° Grid, Weekly| E[GridCellObservation Table]
    D -->|Join on Grid/Week| E
    E -->|Derive: First Arrival (Threshold 3,5,10)| F[Target Variable]
    E -->|Lag: 1-4 Weeks| G[Feature Matrix]
    E -->|VIF Filter: Drop VIF>5| G
    F & G -->|Split: Temporal (2015-2020/21/22)| H[Model Training]
    H -->|XGBoost| I[Model Artifact]
    I -->|SHAP/Permutation| J[Feature Importance]
    I -->|Diebold-Mariano (Temporal Agg)| K[Performance Metrics]
    K -->|Stability Analysis| L[Stability Report]
    I -->|Visualization| M[Regional Maps]
```

## 4. Schema Definitions

See `contracts/` directory for formal YAML schemas.
- `contracts/grid_cell_observation.schema.yaml`: Definition of the processed grid data.
- `contracts/model_metrics.schema.yaml`: Definition of output metrics.