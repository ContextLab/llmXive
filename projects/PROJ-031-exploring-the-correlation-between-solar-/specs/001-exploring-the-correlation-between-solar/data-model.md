# Data Model: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

## Entity Definitions

### SolarFlareEvent
Represents a GOES X-ray flare.
- `timestamp` (datetime): Time of X-ray peak.
- `class` (string): Flare class (e.g., "X1.2", "M5.0").
- `peak_flux` (float): X-ray peak flux in W/m².
- `log10_flux` (float): Log10 transformed peak flux.
- `location` (string): Solar disk location (e.g., "N12W45").
- `source_id` (string): Original record ID from NOAA source.

### CMEEvent
Represents a SOHO/LASCO Coronal Mass Ejection.
- `timestamp` (datetime): Time of CME occurrence.
- `speed` (float): Speed in km/s (may be null).
- `width` (float): Angular width in degrees.
- `direction` (string): Direction (e.g., "halo", "E", "W").
- `source_id` (string): Original record ID from CDAWeb source.

### GeomagneticStorm
Represents a distinct Dst minimum event.
- `timestamp` (datetime): Time of Dst minimum.
- `dst_min` (float): Minimum Dst value in nT.
- `k_index` (float): Kp index at time of minimum.
- `storm_id` (string): Unique identifier for the storm event.
- `is_recurrent` (boolean): Flag indicating if this storm is part of a recurrent period (excluded from analysis if true).

### AlignedEvent
Composite entity linking the above within a ≤3-day window.
- `storm_id` (string): FK to GeomagneticStorm.
- `storm_timestamp` (datetime): Time of Dst minimum.
- `storm_dst` (float): Dst minimum value.
- `flare_timestamp` (datetime): Time of matching flare (or null).
- `flare_log10_flux` (float): Log10 flux of matching flare (or null).
- `cme_timestamp` (datetime): Time of matching CME (or null).
- `cme_speed` (float): Speed of matching CME (or null).
- `match_window_days` (int): Days between storm and solar event (always ≤ 3).
- `flare_missing_flag` (boolean): True if no flare found in window.
- `cme_missing_flag` (boolean): True if no CME found in window.
- `data_quality_score` (integer): **Calculation**: 100 - (count of missing flags). Range [0, 100]. **Usage Note**: This score is for metadata only and is NOT used to weight the regression or correlation analysis to avoid confounding.

## Data Flow

1.  **Ingestion**: Raw files downloaded from NOAA/CDAWeb → `data/raw/`.
2.  **Parsing**: Raw files parsed into `SolarFlareEvent`, `CMEEvent`, `GeomagneticStorm` lists.
3.  **Alignment**:
    - Identify distinct Dst minima (separated by ≥24h recovery).
    - For each storm, search for preceding flare/CME within 3 days.
    - Create `AlignedEvent` row. If no match, flags are set to `True`, values are `NaN`.
4.  **Validation**: `AlignedEvent` list validated against `contracts/aligned_event.schema.yaml`. **Blocking**: If validation fails, the writing of `aligned_events.csv` and the update of the manifest are aborted.
5.  **Storage**: Validated data written to `data/processed/aligned_events.csv`.

## Constraints & Assumptions

- **Missing Data**: Missing values are represented as `NaN` in CSV and `null` in JSON. They are **not** dropped from the dataset.
- **Recurrent Storms**: Storms with <24h recovery are flagged `is_recurrent=True` and excluded from the primary correlation analysis.
- **Time Window**: The 3-day window is fixed. Events outside this window are not matched.
- **Collinearity**: If `flare_log10_flux` and `cme_speed` are highly correlated, VIF will detect this, and the analysis will switch to univariate models.