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
| `depth_km` | float | Depth in kilometers | USGS |
| `magnitude` | float | Magnitude of the earthquake | USGS |
| `location_type` | string | `"land"` or `"ocean"` (derived via global land‑mask) | Derived |

### Pressure Grid Point
| Field | Type | Description | Source |
|---|---|---|---|
| `timestamp` | datetime | UTC date (00:00) | NOAA (verified HuggingFace subset) |
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

### ERA5 Meteorological Covariate (optional for matching)
| Field | Type | Description | Source |
|---|---|---|---|
| `temperature_k` | float | Near‑surface temperature (K) | ERA5 |
| `humidity` | float | Near‑surface relative humidity (%) | ERA5 |
| `timestamp` | datetime | UTC date | ERA5 |
| `latitude` | float | Grid latitude | ERA5 |
| `longitude` | float | Grid longitude | ERA5 |

### Analysis Record (final dataset)
| Field | Type | Description | Source |
|---|---|---|---|
| `event_id` | string | Reference to the earthquake event. |
| `window_type` | string | `"event"` or `"control"` |
| `timestamp` | datetime | Start time of the analysis window. |
| `pressure_anomaly` | number | Deviation from a 30‑day left‑censored moving average. |
| `magnitude` | number | Earthquake magnitude (if event). |
| `region` | string | `"Ring of Fire"` or `"Other"` |
| `is_land` | boolean | True if the event is on land. |
| `climate_index` | string | ENSO or PDO phase label (optional; not populated in pilot). |
| `pdo_phase` | string | `"Positive"`, `"Negative"`, or `"Neutral"` |
| `temperature_k` | number | Temperature covariate used for matching (not in final analysis). |
| `humidity` | number | Humidity covariate used for matching (not in final analysis). |

## Data Pipeline Flow

1. **Raw**  
   - `data/raw/usgs_2013_2023.csv` (USGS catalog)  
   - *No persisted raw pressure NetCDF* – pressure data is streamed from the verified HuggingFace subset at runtime.  
   - `data/raw/enso_pdo.csv` (monthly climate indices)  
   - `data/raw/era5_covariates.parquet` (temperature & humidity for matching).  

2. **Interim**  
   - `data/interim/pressure_grid_coarse_deg.parquet` (interpolated grid)  
   - `data/interim/aligned_events.csv` (earthquake‑grid pairing)  

3. **Processed**  
   - `data/processed/analysis_ready.parquet` (schema = Analysis Record)  

All files are version‑hashed; any change updates the project state artifact map.
