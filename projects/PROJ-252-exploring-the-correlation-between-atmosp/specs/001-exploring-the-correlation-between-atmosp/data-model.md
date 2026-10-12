# Data Model: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Overview

Defines the schema for raw, intermediate, and analysis‑ready artifacts. All files are stored under `data/` with SHA‑256 checksums recorded in project state.

## Entity Definitions

### Earthquake Event
| Field | Type | Description | Source |
|---|---|---|---|
| `event_id` | string | Unique USGS identifier (e.g., `us70001234`) | USGS |
| `timestamp` | datetime | UTC origin time | USGS |
| `latitude` | float | Epicenter latitude (‑90 → 90) | USGS |
| `longitude` | float | Epicenter longitude (‑180 → 180) | USGS |
| `depth_km` | float | Depth in km | USGS |
| `magnitude` | float | Magnitude (Mw or Ml) | USGS |
| `location_type` | string | `"land"` or `"ocean"` (derived via global land‑mask) | Derived |

### Pressure Grid Point
| Field | Type | Description | Source |
|---|---|---|---|
| `timestamp` | datetime | UTC date (00:00) | NOAA |
| `latitude` | float | Grid centre latitude | NOAA |
| `longitude` | float | Grid centre longitude | NOAA |
| `pressure_hpa` | float | Sea‑level pressure (hPa) | NOAA |

### ENSO / PDO Index
| Field | Type | Description | Source |
|---|---|---|---|
| `year` | integer | Calendar year | NOAA |
| `month` | integer | Calendar month (1‑12) | NOAA |
| `enso_phase` | string | `"El Niño"`, `"La Niña"`, or `"Neutral"` | NOAA |
| `pdo_phase` | string | `"Positive"`, `"Negative"`, or `"Neutral"` | NOAA |

### Analysis Record (final dataset)
| Field | Type | Description | Source |
|---|---|---|---|
| `event_id` | string | FK to Earthquake Event | Earthquake |
| `window_type` | string | `"event"` or `"control"` | Derived |
| `timestamp` | datetime | Start of the analysis window | Derived |
| `pressure_anomaly` | float | Deviation from baseline period (30‑day left‑censored moving average) | Derived |
| `magnitude` | float | Earthquake magnitude (if event) | Earthquake |
| `region` | string | `"Ring of Fire"` or `"Other"` | Derived |
| `is_land` | boolean | True if the event is on land | Derived |
| `climate_index` | string | ENSO or PDO phase label (e.g., `"El Niño"`) | ENSO/PDO Index |
| `pdo_phase` | string | PDO phase label (e.g., `"Positive"`) | ENSO/PDO Index |

## Data Pipeline Flow

1. **Raw**  
   - `data/raw/usgs_2013_2023.csv` (USGS catalog)  
   - `data/raw/ncep_global_pressure.nc` (global pressure NetCDF)  
   - `data/raw/enso_pdo.csv` (monthly climate indices)  

2. **Interim**  
   - `data/interim/pressure_grid_1deg.parquet` (interpolated grid)  
   - `data/interim/aligned_events.csv` (earthquake‑grid pairing)  

3. **Processed**  
   - `data/processed/analysis_ready.parquet` (schema = Analysis Record)  

All files are version‑hashed; any change updates the project state artifact map.
