# Data Model: Predicting Avian Song Variation

## 1. Entity Definitions

### 1.1 SongRecord
Represents a single acoustic recording event.
*   `species_id` (string): Unique identifier for the bird species.
*   `location_id` (string): Unique identifier for the recording location.
*   `song_metric_1` (float): Primary song variation metric (e.g., frequency).
*   `song_metric_2` (float): Secondary song variation metric (e.g., duration).
*   `timestamp` (datetime): ISO 8601 timestamp of recording.

### 1.2 EnvironmentRecord
Represents the environmental context for a location.
*   `location_id` (string): Unique identifier (PK, FK to SongRecord).
*   `avg_temp` (float): Average temperature (°C).
*   `total_precip` (float): Total precipitation (mm).
*   `latitude` (float): Latitude in decimal degrees.
*   `longitude` (float): Longitude in decimal degrees.
*   `elevation` (float): Elevation in meters.

### 1.3 ModelResult
Represents the output of the regression analysis.
*   `predictor_name` (string): Name of the independent variable.
*   `coefficient` (float): Estimated effect size.
*   `p_value` (float): Statistical significance.
*   `r_squared` (float): Model fit metric.
*   `model_family` (string): "OLS" or "GLM".
*   `link_function` (string): "identity" or specific GLM link.

## 2. Data Flow

1.  **Raw Input**: `data/raw/acoustic.csv`, `data/raw/climate.csv`, `data/raw/geography.csv`.
2.  **Ingestion**: Merge on `location_id` and `species_id`. Drop rows with missing core variables.
3.  **Processed**: `data/processed/aligned_dataset.parquet`.
4.  **Analysis**:
    *   EDA: Correlation matrix, scatterplots.
    *   Modeling: Coefficients, p-values, R².
5.  **Output**: `output/reports/analysis_report.pdf`, `output/models/model_summary.csv`.

## 3. Schema Constraints

*   **Uniqueness**: `location_id` is unique in `EnvironmentRecord`.
*   **Non-Null**: `species_id`, `location_id`, `song_metric_1`, `avg_temp` are mandatory.
*   **Ranges**: `latitude` [-90, 90], `longitude` [-180, 180].
*   **Distribution**: `song_metric_1` expected to be continuous; if skewed, GLM selected.
