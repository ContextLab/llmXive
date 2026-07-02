# Data Model: Predicting Avian Song Variation with Climatic and Geographic Factors

## Entity Definitions

### 1. SongRecord
Represents a single acoustic recording of a bird.
- **Source**: `data/raw/song_record.csv` (Fetched from Xeno-Canto API).
- **Primary Key**: `record_id` (generated) or composite `(species_id, location_lat, location_lon, timestamp)`.
- **Attributes**:
    - `species_id` (str): Unique identifier for the bird species.
    - `song_metric_1` (float): Primary song metric (e.g., dominant frequency in kHz).
    - `song_metric_2` (float): Secondary song metric (e.g., duration in seconds).
    - `location_lat` (float): Latitude in decimal degrees (WGS84).
    - `location_lon` (float): Longitude in decimal degrees (WGS84).
    - `timestamp` (str): ISO 8601 timestamp of recording (optional).

### 2. ClimateSnapshot
Represents environmental conditions at a specific location.
- **Source**: `data/raw/climate_snapshot.csv` (Extracted from WorldClim v2.1 raster).
- **Primary Key**: `location_id` (generated) or composite `(location_lat, location_lon, date)`.
- **Attributes**:
    - `location_lat` (float): Latitude in decimal degrees (WGS84).
    - `location_lon` (float): Longitude in decimal degrees (WGS84).
    - `temperature` (float): Mean temperature (°C).
    - `precipitation` (float): Total precipitation (mm).
    - `elevation` (float): Elevation above sea level (m).
    - `date` (str): Date of measurement (ISO 8601).

### 3. AnalysisDataset
The merged entity resulting from the join of `SongRecord` and `ClimateSnapshot`.
- **Source**: `data/processed/analysis_dataset.parquet`.
- **Primary Key**: `record_id` (from `SongRecord`).
- **Attributes**:
    - Inherits all attributes from `SongRecord`.
    - Inherits all attributes from `ClimateSnapshot`.
    - `match_status` (str): "matched" or "excluded".
    - `distance_km` (float): Distance between song location and climate grid cell center (if spatial join used).

## Data Flow

1.  **Ingestion**: Fetch `SongRecord` from Xeno-Canto and `ClimateSnapshot` from WorldClim v2.1.
2.  **Validation**: Check for required columns and valid numeric ranges (against `song_record.schema.yaml`, `climate_snapshot.schema.yaml`).
3.  **Alignment**:
    -   Reproject coordinates to WGS84.
    -   **Join**: Exact match on `species_id` + **Nearest Grid Cell Extraction** (Bilinear with Nearest Neighbor fallback) on coordinates.
4.  **Transformation**:
    -   Handle missing values (impute or exclude).
    -   Calculate derived metrics (e.g., distance).
    -   **Filter**: Exclude rows with `match_status` = "excluded".
5.  **Sampling**: If total rows > 50k, apply stratified random sample.
6.  **Output**: Save `AnalysisDataset` as Parquet.
7.  **Analysis**: Run EDA and Modeling on `AnalysisDataset`.

## Constraints & Validation Rules

-   **Coordinates**: Must be within valid lat/lon ranges (-90 to 90, -180 to 180).
-   **Song Metrics**: Must be positive floats (frequency > 0, duration > 0).
-   **Climate Variables**: Must be numeric; missing values handled per policy.
-   **Uniqueness**: No duplicate rows in `AnalysisDataset` after join.
