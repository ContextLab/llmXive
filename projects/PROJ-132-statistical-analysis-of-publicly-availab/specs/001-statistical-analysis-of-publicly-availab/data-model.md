# Data Model: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## 1. Entity Definitions

### MigrationRecord
Represents a single bird observation from the eBird dataset.
- `species_id` (str): Unique identifier for the species (e.g., "TURDUS-MIGRATORIOUS").
- `latitude` (float): Latitude of the observation (WGS84).
- `longitude` (float): Longitude of the observation (WGS84).
- `date` (date): Date of observation (YYYY-MM-DD).
- `count` (int): Number of individuals observed.
- `checklist_id` (str): Unique checklist ID from eBird.
- `grid_cell` (str): "lat_lon" formatted string (e.g., "45.5_-75.0") derived from 0.5° grid.

### PhenologyMetric
Computed metric for a species-grid cell-year combination.
- `species_id` (str)
- `grid_cell` (str)
- `year` (int)
- `first_arrival_date` (date): First arrival in spring window. **Note**: Retained for archival, excluded from stopover modeling.
- `median_arrival_date` (date): Median arrival date.
- `stopover_duration` (float): Days between 10th and 90th percentile arrival dates.
- `observation_count` (int): Total observations in the cell/year.
- `data_quality` (str): "sufficient" or "insufficient" (if count < 5).

### ClimateVariable
Climate measurements for a grid cell-week.
- `grid_cell` (str)
- `week_start` (date): Start of the week.
- `mean_temperature` (float): Average temperature (°C).
- `total_precipitation` (float): Total precipitation (mm).
- `extreme_weather_index` (float): Derived index (e.g., days > 30°C).
- `source` (str): "Daymet".

### Trajectory
Weekly centroid sequence for a species-year (Discrete Method).
- `species_id` (str)
- `year` (int)
- `centroids` (list[dict]): List of `{"lat": float, "lon": float}` for each week.
- `shift_vector` (dict): `{"magnitude": float, "direction": float}` (radians, mean displacement).
- `p_value` (float): Significance from block bootstrap.

### ProvenanceFile
Links processed data to original sources.
- `processed_row_id` (str): Unique ID in processed dataset.
- `original_checklist_id` (str): Original eBird checklist ID.
- `original_row_index` (int): Row index in the raw file.
- `filter_reason` (str): "sufficient", "insufficient", "date_filter", "species_filter".

## 2. Data Flow

1. **Raw Ingestion**: `download.py` fetches EBD (CSV) and Daymet (Parquet stream) to `data/raw/`.
2. **Preprocessing**: `preprocess.py` reads raw data, filters for migratory species (2020-2024), aggregates to 0.5° grid, and computes `PhenologyMetric`.
3. **Climate Join**: `preprocess.py` joins `PhenologyMetric` with `ClimateVariable` on `grid_cell` and `week`.
4. **Provenance Generation**: `preprocess.py` generates `data/provenance/row_mapping.json` linking processed rows to original `checklist_id`s.
5. **Model Input**: `gamm.py` reads filtered `PhenologyMetric` (data_quality="sufficient") and fits models.
6. **Output**: `analysis/correlation.py` generates final statistics; `analysis/routes.py` generates trajectory shifts.

## 3. Validation Rules

- **Grid Cell**: Must be "lat_lon" with 1 decimal precision (0.5°).
- **Date Range**: All dates must be between 2020-01-01 and 2024-12-31.
- **Missing Data**: `first_arrival_date` is NULL if `observation_count` < 5.
- **Geographic Bounds**: Latitude [-90, 90], Longitude [-180, 180].

