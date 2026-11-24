# Data Model: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Overview
Defines schemas for raw, intermediate, and analysis‑ready artifacts. All files reside under `data/` and are version‑hashed.

### Earthquake Event (raw USGS catalog)
| Field | Type | Description |
|---|---|---|
| `event_id` | string | USGS event identifier (e.g., `us7000abcd`). |
| `timestamp` | datetime | UTC origin timestamp (ISO‑8601). |
| `latitude` | float | Epicenter latitude (‑90 → 90). |
| `longitude` | float | Epicenter longitude (‑180 → 180). |
| `depth_km` | float | Depth in kilometers. |
| `magnitude` | float | Moment magnitude. |
| `location_type` | string | `"land"` or `"ocean"` (derived via land‑mask). |

### Pressure Grid Point *(Active)*
| Field | Type | Description |
|---|---|---|
| `timestamp` | datetime | UTC date (00:00). |
| `latitude` | float | Grid centre latitude. |
| `longitude` | float | Grid centre longitude. |
| `pressure_hpa` | float | Sea‑level pressure (hPa). |

### ENSO / PDO Index *(Deferred)*
| Field | Type | Description |
|---|---|---|
| `year` | integer | Calendar year. |
| `month` | integer | Calendar month (1‑12). |
| `enso_phase` | string | `"El Niño"`, `"La Niña"` or `"Neutral"`. |
| `pdo_phase` | string | `"Positive"`, `"Negative"` or `"Neutral"`. |

### ERA5 Covariates *(Deferred)*
| Field | Type | Description |
|---|---|---|
| `timestamp` | datetime | UTC date. |
| `latitude` | float | Grid latitude. |
| `longitude` | float | Grid longitude. |
| `temperature_k` | float | Near‑surface temperature (K). |
| `humidity` | float | Relative humidity (%). |

### Analysis Record *(Final, when all data are present)*
| Field | Type | Description |
|---|---|---|
| `event_id` | string | Reference to earthquake event. |
| `window_type` | string | `"event"` or `"control"`. |
| `timestamp` | datetime | Start time of the analysis window. |
| `pressure_anomaly` | number | Deviation from left‑censored moving average. |
| `magnitude` | number | Earthquake magnitude (null for control). |
| `region` | string | `"Ring of Fire"` or `"Other"`. |
| `is_land` | boolean | True if the event is on land. |
| `climate_index` | string | ENSO or PDO phase label (optional; not populated in pilot). |
| `pdo_phase` | string | `"Positive"`, `"Negative"` or `"Neutral"`. |
| `temperature_k` | number | Matching temperature (used for control matching). |
| `humidity` | number | Matching humidity (used for control matching). |

## Data Pipeline Flow
1. **Raw** – `data/raw/usgs_all_month.csv` (USGS catalog).  
2. **Raw Pressure** – streamed from NOAA NCEP/NCAR reanalysis (no persistent file).  
3. **Interim** – `data/interim/earthquakes_clean.parquet` (validated, deduplicated, ocean‑masked).  
4. **Processed** – `data/processed/analysis_ready.parquet` (schema above; contains pressure anomalies and control windows).  

All files are accompanied by SHA‑256 checksums stored in the project state file.

---

