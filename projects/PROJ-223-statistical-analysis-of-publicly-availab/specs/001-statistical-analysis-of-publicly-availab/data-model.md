# Data Model: Statistical Analysis of Publicly Available Traffic Accident Data

## Entity Relationship Overview

The data model consists of three primary entities: `AccidentRecord`, `WeatherObservation`, and the derived `MergedDataset`.

### 1. AccidentRecord
Represents a single traffic accident event.
- **Source**: FARS dataset (NHTSA).
- **Key Attributes**:
  - `accident_id`: Unique identifier (String/Int).
  - `severity`: Ordinal outcome (0=Property, 1=Injury, 2=Fatality).
  - `timestamp`: Date and time of accident (DateTime).
  - `location_lat`: Latitude (Float).
  - `location_lon`: Longitude (Float).
  - `road_type`: Categorical (e.g., Highway, Residential).
  - `vehicle_type`: Categorical (e.g., Car, Truck, Motorcycle).
  - `hour`: Extracted hour (Int).
  - `day_of_week`: Extracted day (Int 0-6).

### 2. WeatherObservation
Represents weather conditions at a specific time and location.
- **Source**: NOAA GHCN-Daily dataset.
- **Key Attributes**:
  - `station_id`: Weather station identifier (String).
  - `date`: Date of observation (Date).
  - `precipitation`: Total precipitation (Float, mm).
  - `visibility`: Visibility distance (Float, km).
  - `temperature`: Average temperature (Float, °C).
  - `station_lat`: Station latitude (Float).
  - `station_lon`: Station longitude (Float).

### 3. MergedDataset
The analytical dataset resulting from joining `AccidentRecord` and `WeatherObservation`.
- **Join Key**: Temporal proximity (e.g., same day or nearest hour) and spatial proximity (e.g., within 50km radius).
- **Derived Columns**:
  - `weather_precipitation`: Mapped from `WeatherObservation`.
  - `weather_visibility`: Mapped from `WeatherObservation`.
  - `weather_temperature`: Mapped from `WeatherObservation`.
  - `is_missing_weather`: Boolean flag for records where weather data was not found (to be imputed).

## Data Dictionary

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `severity` | Int (Ordinal) | 0=Property, 1=Injury, 2=Fatality | 0 ≤ x ≤ 2 |
| `precipitation` | Float | Total precipitation (mm) | ≥ 0 |
| `visibility` | Float | Visibility (km) | ≥ 0 |
| `temperature` | Float | Temperature (°C) | No specific range |
| `hour` | Int | Hour of day (0-23) | 0 ≤ x ≤ 23 |
| `day_of_week` | Int | Day of week (0-6) | 0 ≤ x ≤ 6 |
| `road_type` | String | Categorical road type | Non-null |
| `vehicle_type` | String | Categorical vehicle type | Non-null |
| `sample_weight` | Float | Weight for stratified sampling | ≥ 0 |

## Transformation Logic

1. **Ingestion**: Load raw CSV/Parquet files.
2. **Cleaning**:
   - Drop rows with missing `severity`, `accident_id`, `location_lat`, or `location_lon`.
   - **Missing Weather**: Do NOT drop rows with missing `precipitation`, `visibility`, or `temperature`. Instead, flag them for imputation.
3. **Imputation**:
   - Apply Multiple Imputation by Chained Equations (MICE) using `sklearn.impute.IterativeImputer` to fill missing weather variables based on other predictors.
   - No Winsorization is applied to preserve the distribution of extreme weather events.
4. **Encoding**:
   - Convert `severity` to ordinal integer.
   - One-hot encode `road_type` and `vehicle_type` for model input.
5. **Merging**:
   - Join on `date` (from `timestamp`) and spatial proximity.
   - Retain only rows with successful accident ID match; weather data may be missing initially but will be imputed.
6. **Sampling**:
   - If `n_rows` > 5,000,000, apply stratified sampling (strata=`severity`) to reduce to ~5M rows.
