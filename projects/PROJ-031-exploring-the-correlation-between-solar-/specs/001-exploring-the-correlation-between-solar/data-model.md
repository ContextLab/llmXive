# Data Model: Solar-Geomagnetic Correlation

## Overview

This document defines the data structures used for ingesting, aligning, and analyzing solar flare, CME, and geomagnetic storm data. The model supports missing data handling and ensures traceability to source records.

## Entity Definitions

### 1. SolarFlareEvent
Represents a GOES X-ray flare event.
-   `event_id`: Unique identifier (Source: NOAA SWPC).
-   `timestamp`: ISO 8601 datetime of peak flux.
-   `peak_flux_wm2`: Float, X-ray peak flux in W/m².
-   `flare_class`: String (e.g., "M5.3", "X2.1").
-   `log10_flux`: Float, calculated as $\log_{10}(peak\_flux\_wm2)$.
-   `source_location`: String (e.g., "S15W30").
-   `data_quality_flag`: Boolean, `True` if data is valid.

### 2. CMEEvent
Represents a SOHO/LASCO Coronal Mass Ejection.
-   `event_id`: Unique identifier (Source: CDAWeb).
-   `timestamp`: ISO 8601 datetime of first appearance.
-   `speed_kms`: Float, CME speed in km/s. **Nullable**.
-   `width_degrees`: Float, angular width.
-   `direction`: String (e.g., "Earth-directed").
-   `data_quality_flag`: Boolean, `True` if speed is available.

### 3. GeomagneticStorm
Represents a geomagnetic storm event.
-   `event_id`: Unique identifier.
-   `timestamp_min`: ISO 8601 datetime of Dst minimum.
-   `dst_min`: Float, minimum Dst index in nT.
-   `kp_max`: Float, maximum Kp index during storm.
-   `is_severe`: Boolean, `True` if `dst_min` ≤ -100.
-   `is_recurrent`: Boolean, `True` if storm is within 24h of a previous storm (excluded from primary analysis).

### 4. AlignedEvent
Composite entity linking the three sources.
-   `storm_id`: Reference to `GeomagneticStorm`.
-   `flare_id`: Reference to `SolarFlareEvent` (Nullable).
-   `cme_id`: Reference to `CMEEvent` (Nullable).
-   `time_diff_hours`: Float, time difference between storm min and solar event.
-   `window_valid`: Boolean, `True` if `time_diff_hours` ≤ 72 (3 days).
-   `flare_flux`: Float (from linked flare, or `null`).
-   `cme_speed`: Float (from linked CME, or `null`).
-   `missing_flare_flag`: Boolean.
-   `missing_cme_flag`: Boolean.
-   `source_manifest_ref`: String, reference to `data/source_manifest.yaml` entry.

## Data Flow

1.  **Ingestion**: Raw CSV/JSON from NOAA/CDAWeb → `data/raw/`.
2.  **Parsing**: Raw files → `SolarFlareEvent`, `CMEEvent`, `GeomagneticStorm` objects.
3.  **Alignment**:
    -   Identify all `GeomagneticStorm` minima.
    -   For each storm, search for flares/CMEs within ±3 days (preceding).
    -   Create `AlignedEvent`. If no match, set `flare_id`/`cme_id` to `null` and set flags.
    -   Filter out `is_recurrent` storms for primary correlation analysis (but retain in dataset).
4.  **Output**: `data/processed/aligned_events.csv`.

## Missing Data Handling

-   **Strategy**: Retain events with missing predictors.
-   **Implementation**: `null` values in CSV; specific flags (`missing_flare_flag`, `missing_cme_flag`) set to `True`.
-   **Analysis Impact**:
    -   Flare-Dst correlation: Excludes rows where `missing_flare_flag` is `True`.
    -   CME-Dst correlation: Excludes rows where `missing_cme_flag` is `True`.
    -   Joint analysis: Excludes rows where either flag is `True`.
