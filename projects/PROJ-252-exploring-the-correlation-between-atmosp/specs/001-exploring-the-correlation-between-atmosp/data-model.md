# Data Model: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in `data/` with checksums.

## Entity Definitions

### Earthquake Event
Represents a single seismic event from the USGS catalog.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `event_id` | string | Unique USGS event ID (e.g., `us70001234`) | USGS |
| `timestamp` | datetime | UTC time of origin | USGS |
| `latitude` | float | Epicenter latitude (-90 to 90) | USGS |
| `longitude` | float | Epicenter longitude (-180 to 180) | USGS |
| `depth_km` | float | Depth in kilometers | USGS |
| `magnitude` | float | Magnitude (Mw or Ml) | USGS |
| `location_type` | string | "land" or "ocean" (derived) | Derived |

### Pressure Grid Point
Represents a pressure measurement at a specific grid point and time.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `timestamp` | datetime | UTC date (00:00:00) | NOAA |
| `latitude` | float | Grid center latitude | NOAA |
| `longitude` | float | Grid center longitude | NOAA |
| `pressure_hpa` | float | Sea-level pressure in hPa | NOAA |

### Analysis Record
The joined record used for statistical testing.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `event_id` | string | FK to Earthquake Event | Earthquake |
| `window_type` | string | "event" or "control" | Derived |
| `timestamp` | datetime | Start of the window | Derived |
| `pressure_anomaly` | float | Deviation from 30-day mean | Derived |
| `magnitude` | float | Event magnitude | Earthquake |
| `region` | string | "Ring of Fire" or "Other" | Derived |
| `is_land` | boolean | True if epicenter is on land | Derived |

## Data Pipeline Flow

1.  **Raw**: `data/raw/usgs_2013_2023.csv`, `data/raw/ncep_*.zip`
2.  **Interim**: `data/interim/pressure_grid_1deg.parquet`, `data/interim/aligned_events.csv`
3.  **Processed**: `data/processed/analysis_ready.parquet` (Final schema: Analysis Record)
