# Data Model: Traffic-Weather Severity Analysis

## 1. Entity-Relationship Overview

The data model consists of three primary entities: `AccidentRecord`, `WeatherStationData`, and the derived `MergedDataset`.

### AccidentRecord (Source: FARS)
Represents a single traffic crash event.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `accident_id` | str | Unique identifier from FARS | Primary Key |
| `timestamp` | datetime | Date and time of accident | Not Null |
| `lat` | float | Latitude (WGS84) | Not Null, [-90, 90] |
| `lon` | float | Longitude (WGS84) | Not Null, [-180, 180] |
| `severity_raw` | int | Raw FARS severity code | 0-9 |
| `severity` | int | Encoded ordinal (0, 1, 2) | 0=Prop, 1=Injury, 2=Fatal |
| `road_type` | str | Road classification | Not Null |
| `vehicle_type` | str | Vehicle classification | Not Null |
| `state` | str | US State code | Not Null |

### WeatherStationData (Source: NOAA ISD)
Represents meteorological conditions at a specific station.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `station_id` | str | NOAA Station ID | Primary Key |
| `timestamp` | datetime | Observation time | Not Null |
| `lat` | float | Station Latitude | Not Null |
| `lon` | float | Station Longitude | Not Null |
| `precipitation_amount` | float | Precipitation (inches) | >= 0.0 |
| `visibility_miles` | float | Visibility (miles) | >= 0.0 |
| `temperature_f` | float | Temperature (Fahrenheit) | No bounds |

### MergedDataset (Derived)
The unified dataset for analysis.

| Field | Type | Source | Description |
| :--- | :--- | :--- | :--- |
| `accident_id` | str | AccidentRecord | Link to original record |
| `timestamp` | datetime | AccidentRecord | Accident time |
| `lat` | float | AccidentRecord | Accident location |
| `lon` | float | AccidentRecord | Accident location |
| `severity` | int | AccidentRecord | Encoded outcome |
| `road_type` | str | AccidentRecord | Control variable |
| `vehicle_type` | str | AccidentRecord | Control variable |
| `station_id` | str | WeatherStationData | Source station |
| `distance_km` | float | Calculated | **Distance to station** (Control for spatial error) |
| `precipitation_amount` | float | WeatherStationData | Predictor |
| `visibility_miles` | float | WeatherStationData | Predictor |
| `temperature_f` | float | WeatherStationData | Predictor |
| `match_method` | str | Logic | 'nearest' or 'interpolated' |

### ExcludedRecordsSummary (Derived)
**New Artifact**: Summary of records excluded due to missing weather data (for Bias Quantification).

| Field | Type | Description |
| :--- | :--- | :--- |
| `severity_level` | int | Encoded severity (0, 1, 2) or "Unknown" |
| `count` | int | Number of excluded records with this severity |
| `percentage` | float | Percentage of total excluded records |

## 2. Transformation Logic

### Severity Encoding (FR-002)
- **Input**: `severity_raw` (FARS code).
- **Mapping**:
  - `0`, `1` (No Injury, Property Damage Only) → `0`
  - `2` through `8` (Minor, Serious, Severe, Fatal but not [deferred]) → `1` (Injury)
  - `9` (Fatality) → `2` (Fatality)
- **Exclusion**: Any record with `severity_raw` not in the mapped set or missing is excluded and logged in `ExcludedRecordsSummary`.

### Spatial-Temporal Merge (FR-001)
1.  **Filter**: Select NOAA stations within 100km of FARS centroids (Pre-filtering).
2.  **Match**: For each accident, find the nearest station within 50km and within ±1 hour.
3.  **Selection**:
    - If multiple readings: Use linear interpolation to the exact accident time, or the nearest hour if interpolation fails.
4.  **Fallback**: If no station within 50km:
    - **Action**: Record is **excluded** from the `MergedDataset`.
    - **Logging**: Record is added to `ExcludedRecordsSummary` with its `severity` (if known) or "Unknown".
    - **Bias Check**: This step enables the Bias Quantification analysis.
5.  **Match Method Assignment**:
    - **Logic**: If the time difference between the accident timestamp and the weather observation is > 0 minutes (i.e., interpolation was used), set `match_method` = "interpolated".
    - **Logic**: If the time difference is 0 minutes (exact match), set `match_method` = "nearest".
    - **Validation**: `ingest.py` must assert that `match_method` is populated for every record in the `MergedDataset`.

### Missing Data Handling
- **Severity**: Excluded from model, logged in `ExcludedRecordsSummary`.
- **Weather**: If `precipitation`, `visibility`, or `temperature` is missing after the merge, the record is excluded from the model and logged in `ExcludedRecordsSummary`.
- **Controls**: If `road_type` or `vehicle_type` is missing, a "Unknown" category is created.

## 3. Data Quality Metrics

- **Coverage Rate (SC-001)**: `(Total Records with Valid Weather) / (Total Valid Accident Records)`. Target: ≥ 85%.
- **Convergence Rate (SC-002)**: `(Successful Model Fits) / (Total Model Fits)`. Target: ≥ 95%.
- **Stability (SC-003)**: **Note**: Spec requires binary sweep stability. Plan implements continuous subset stability as primary robustness + binary sweep as distinct hypothesis.
- **Bias Quantification**: Chi-square p-value comparing `MergedDataset` severity distribution vs. `ExcludedRecordsSummary`.