# Data Model: Ambient Temperature Influence on Moral Decision Speed

## Entity-Relationship Overview

The data model consists of three primary entities: `MoralResponse`, `TemperatureRecord`, and `MergedDataset`. The `MergedDataset` is the canonical input for statistical modeling.

### 1. MoralResponse (Raw)
Source: Moral Machine Dataset (CSV)
- **Entity**: A single decision event.
- **Key Fields**:
  - `response_id`: Unique identifier (string).
  - `participant_id`: Unique participant identifier (string).
  - `latitude`: Decimal (float) OR `city`: String, `country`: String (if GPS missing).
  - `longitude`: Decimal (float) OR `country`: String (if GPS missing).
  - `timestamp`: ISO 8601 datetime.
  - `response_time_ms`: Integer (milliseconds).
  - `age`: Integer.
  - `gender`: String (categorical).
  - `dilemma_id`: String.
  - `choice`: String ("save_many", "save_few").
  - `cultural_region`: String.

### 2. TemperatureRecord (Raw)
Source: NOAA GHCN-Daily / ERA5-Land (Parquet/NetCDF)
- **Entity**: Daily or Hourly temperature observation.
- **Key Fields**:
  - `station_id` (or `grid_id`): String.
  - `latitude`: Decimal (float).
  - `longitude`: Decimal (float).
  - `timestamp`: ISO 8601 datetime (daily or hourly).
  - `temperature_celsius`: Float.
  - `quality_flag`: String (valid/invalid).

### 3. MergedDataset (Processed)
Source: Join of `MoralResponse` and `TemperatureRecord`.
- **Entity**: The analysis-ready dataset.
- **Key Fields**:
  - `response_id`: PK.
  - `participant_id`: FK.
  - `log_response_time`: Float (log-transformed).
  - `temperature_celsius`: Float (matched).
  - `distance_km`: Float (distance to station/grid).
  - `dilemma_complexity`: Float (derived from static attributes, e.g., |lives_a - lives_b|).
  - `time_of_day`: String (categorical).
  - `age`: Integer.
  - `gender`: String.
  - `cultural_region`: String.
  - `match_quality`: String ("high", "low", "excluded").

## Data Quality Rules

1. **Missing Location**: Records with `latitude`/`longitude` NULL (or missing city/country) are excluded.
2. **Impossible Time**: Records with `response_time_ms` < 100 or > 3 SD from the median are excluded (Empirical Outlier Detection).
3. **Station Distance**: Records with `distance_km` > 100 are flagged as "low confidence" and excluded from primary modeling.
4. **Temperature Gap**: If the time difference between Moral Response and nearest Temperature record > 2 hours (or 1 day), the record is excluded.

## Derived Variables

- **`log_response_time`**: `ln(response_time_ms)`. Used for normality.
- **`dilemma_complexity`**: Calculated as `abs(lives_a - lives_b)` or a similar conflict metric. Derived solely from static attributes to avoid tautology with response time.
- **`time_of_day`**: Categorized as "morning" (06-12), "afternoon" (12-18), "evening" (18-00), "night" (00-06).
- **`temperature_squared`**: `temperature_celsius^2` (for non-linearity check).

## Storage Format

- **Raw**: CSV (Moral Machine), Parquet/NetCDF (NOAA/ERA5).
- **Processed**: Parquet (`data/processed/merged_dataset.parquet`).
- **Logs**: JSON (`results/logs/data_quality_log.json`).