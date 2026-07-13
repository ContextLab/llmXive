# Data Model: Statistical Analysis of Publicly Available Weather Data for Extreme Event Prediction

## 1. Entity Definitions

### 1.1 Station
Represents a weather monitoring location.
- `station_id`: Unique string identifier (e.g., "USC00012345").
- `latitude`: Float (degrees).
- `longitude`: Float (degrees).
- `elevation`: Float (meters).
- `total_missing_pct`: Float (0.0 to 1.0).
- `max_contiguous_gap_days`: Integer.
- `status`: Enum ["active", "excluded"].

### 1.2 ExtremeEvent
Represents a single day where a threshold is exceeded.
- `station_id`: String (FK to Station).
- `date`: Date (YYYY-MM-DD).
- `magnitude`: Float (precipitation amount - threshold).
- `threshold_value`: Float (the 95th percentile for that station).
- `is_exceedance`: Boolean (always True for this entity).

### 1.3 ModelFit
Represents the result of a statistical model.
- `model_type`: Enum ["independent_gpd", "spatial_gpd", "fallback_gpd"].
- `station_id`: String (or "global" for spatial).
- `parameters`: Dictionary (e.g., `{"shape": 0.1, "scale": 2.5}`).
- `convergence_status`: Enum ["success", "failed", "timeout"].
- `computation_time`: Float (seconds).
- `fitted_on`: String (date range, e.g., "2000-2015").

### 1.4 EvaluationMetric
Represents a performance measure.
- `metric_name`: Enum ["Brier", "RMSE", "Coverage"].
- `value`: Float.
- `model_type`: Enum ["independent_gpd", "spatial_gpd", "fallback_gpd"].
- `test_period`: String (e.g., "2019-2020").
- `station_id`: String (optional, for per-station metrics).

## 2. Data Flow

1. **Ingestion**: Raw GHCN-Daily CSV/Parquet -> `Station` + `RawTimeSeries`.
2. **Preprocessing**: `RawTimeSeries` -> Filtered `Station` (exclusions) -> Imputed `TimeSeries` -> `ExtremeEvent` (via thresholding).
3. **Modeling**: `ExtremeEvent` -> `ModelFit` (Independent) & `ModelFit` (Spatial).
4. **Evaluation**: `ModelFit` + `ExtremeEvent` (Test Set) -> `EvaluationMetric`.
5. **Visualization**: `EvaluationMetric` + `ExtremeEvent` -> Diagnostic Plots.

## 3. Schema Constraints

- **Station**: Must have valid lat/long coordinates.
- **ExtremeEvent**: `magnitude` > 0.0.
- **ModelFit**: `convergence_status` must be recorded for every fit.
- **EvaluationMetric**: `value` must be finite (no NaN/Inf).

## 4. File Formats

- **Input**: Parquet (from HuggingFace) or CSV (raw).
- **Intermediate**: CSV (for processed time series and extremes).
- **Output**: JSON (for metrics and model parameters).
- **Visuals**: PNG (for plots).