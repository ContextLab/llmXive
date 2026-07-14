# Data Model: Atmospheric River Gravity Correlation

This document defines the core entities, attributes, and relationships used throughout the `PROJ-267-exploring-the-relationship-between-atmos` project. It serves as the schema specification for data ingestion, preprocessing, analysis, and output artifacts.

## 1. Overview

The project investigates the statistical correlation between Atmospheric River (AR) intensity and local gravity anomalies measured by the GRACE-FO satellite mission. [UNRESOLVED-CLAIM: c_e56d1d0a — status=not_enough_info] The data flow transforms raw satellite and catalog data into a merged monthly time series, which is then subjected to correlation analysis.

The primary entities are:
1. **AR Event**: A discrete atmospheric river occurrence from the NOAA CPC catalog.
2. **Gravity Anomaly**: A processed mass change measurement from GRACE-FO mascon solutions.
3. **Correlation Result**: The statistical output of the analysis comparing AR intensity and gravity anomalies.

## 2. Entity Definitions

### 2.1 AR Event (Raw & Aggregated)

Represents an individual atmospheric river event detected by NOAA CPC, and its aggregated monthly properties.

**Source**: NOAA CPC Atmospheric River Catalog
**Granularity**: Daily (Raw) -> Monthly (Aggregated)

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `event_id` | string | Unique identifier for the AR event (from source) | Non-empty, unique per raw event |
| `start_date` | date | Start date of the event (YYYY-MM-DD) | Valid ISO date |
| `end_date` | date | End date of the event (YYYY-MM-DD) | >= start_date |
| `max_iwt` | float | Maximum Integrated Water Vapor Transport (kg/m/s) | > 0 |
| `max_iwt_direction` | float | Direction of max IWT (degrees) | [0, 360) |
| `duration_days` | int | Duration of the event in days | >= 1 |
| `region` | string | Geographic region code (e.g., "West_Coast") | Must match `region` in Gravity Anomaly |
| `monthly_aggregate` | float | Sum of IWT or count of events for the month | Aggregated value |

**Aggregation Logic**:
- Events are assigned to a month based on `start_date`.
- For monthly aggregation, `monthly_aggregate` represents the **Integrated Water Vapor Transport (IWVT) Sum** for all events in that month within the target region (35°N-50°N, 120°W-125°W).
- Months with zero events are excluded from correlation calculations but may be logged.

### 2.2 Gravity Anomaly

Represents the processed gravity field variation (mass change) derived from GRACE-FO mascon solutions.

**Source**: CSR/GRACE-FO Mascon Solutions (Level 3)
**Granularity**: Monthly (Processed)

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `month` | date | Reference month (YYYY-MM-01) | Valid ISO month start |
| `region` | string | Target region identifier (e.g., "West_Coast") | Matches AR Event region |
| `mascon_id` | string | Identifier for the specific mascon grid cell | Unique per cell |
| `lat` | float | Latitude of mascon center | [35.0, 50.0] for target region |
| `lon` | float | Longitude of mascon center | [-125.0, -120.0] for target region |
| `equivalent_water_height` | float | Equivalent Water Height (EWH) in mm | Unit: mm |
| `uncertainty` | float | Measurement uncertainty (1-sigma) in mm | >= 0 |
| `c20_corrected` | boolean | Flag indicating C20 coefficient replacement applied | True |
| `degree_1_corrected` | boolean | Flag indicating Degree-1 correction applied | True |
| `smoothed` | boolean | Flag indicating Gaussian smoothing applied | True |
| `monthly_value` | float | Final aggregated monthly gravity anomaly value | Derived from EWH over region |

**Preprocessing Steps**:
1. **Degree-1 Correction**: Applied to account for center of mass motion.
2. **C20 Replacement**: Replaced with values from SLR (Satellite Laser Ranging).
3. **Gaussian Smoothing**: Applied to reduce noise (spatial scale ~300-500km).
4. **Regional Aggregation**: Values are averaged or summed over the defined West Coast bounding box.

### 2.3 Correlation Result

Represents the statistical outcome of comparing AR intensity and Gravity Anomalies.

**Source**: Analysis Pipeline (04_correlation.py, 05_bootstrap_correction.py)
**Granularity**: Per Lag Window, Per Region Type

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `analysis_id` | string | Unique identifier for the analysis run | UUID or hash |
| `region_type` | string | "target" or "control" | Enum |
| `lag_months` | int | Time lag between AR event and gravity response | [0, 3] |
| `pearson_r` | float | Pearson correlation coefficient | [-1, 1] |
| `p_value` | float | Raw p-value for correlation | [0, 1] |
| `p_value_corrected` | float | Multiple-comparison corrected p-value | [0, 1] |
| `significant` | boolean | Is p_value_corrected < 0.05? | Derived |
| `ci_lower` | float | Lower bound of 95% Bootstrap CI | < pearson_r |
| `ci_upper` | float | Upper bound of 95% Bootstrap CI | > pearson_r |
| `n_effective` | int | Effective sample size after autocorrelation correction | >= 1 |
| `noise_floor_sigma` | float | Noise floor threshold (3x uncertainty) | >= 0 |
| `signal_magnitude` | float | Magnitude of the observed correlation signal | Derived |

## 3. Data Flow & File Artifacts

The entities map to specific files in the project structure:

1. **Raw Data**:
 - `data/raw/grace-fo/`: GRACE-FO mascon NetCDF/CSV files.
 - `data/raw/noaa-ar/`: NOAA CPC AR Catalog CSV files.

2. **Processed Data**:
 - `data/processed/merged_monthly.csv`:
 - Combines `Gravity Anomaly` (monthly_value) and `AR Event` (monthly_aggregate).
 - Columns: `month`, `region`, `gravity_anomaly_mm`, `ar_intensity_iwvt_sum`, `n_events`.
 - Schema validated against `contracts/dataset.schema.yaml`.

3. **Analysis Output**:
 - `data/processed/correlation_results.csv` (or JSON):
 - Contains `Correlation Result` entities.
 - Schema validated against `contracts/output.schema.yaml`.

## 4. Constraints & Edge Cases

- **Missing Data**: If a month has no GRACE-FO data or no AR events, it is logged and excluded from correlation calculations (unless imputation is specified, which is currently not the case).
- **Region Alignment**: Gravity anomalies are calculated only for mascons falling strictly within the West Coast bounding box (35°N-50°N, 120°W-125°W).
- **Significance**: A result is considered "significant" only if the Bonferroni (or similar) corrected p-value is < 0.05.
- **Null Results**: If the correlation coefficient is < 0.1 or not statistically significant, the result is still recorded as a `Correlation Result` with `significant=False`.

## 5. References

- **GRACE-FO**: Saveen et al., "GRACE-FO Level 3 Mascon Solutions", CSR.
- **NOAA AR Catalog**: Ralph et al., "Atmospheric River Tracking Method Intercomparison Project".
- **Statistical Methods**: Newey-West standard errors, Bootstrap resampling (1000 iterations).