# Data Model: Atmospheric River Gravity Correlation

This document defines the core entities and data structures used throughout the `PROJ-267` pipeline.
It serves as the contract for data ingestion, preprocessing, analysis, and visualization tasks.

## 1. Core Entities

### 1.1 AR Event (Atmospheric River Event)
Represents a single atmospheric river occurrence as recorded in the NOAA CPC Atmospheric River Catalog.

**Source**: NOAA CPC AR Catalog (via ERDDAP)
**Granularity**: Event-level (individual storm passage)
**Temporal Resolution**: Event start/end timestamps (aggregated to monthly for analysis)

**Fields**:
- `event_id` (str): Unique identifier for the AR event.
- `start_time` (datetime): ISO 8601 timestamp of event onset.
- `end_time` (datetime): ISO 8601 timestamp of event termination.
- `peak_iwvt` (float): Peak Integrated Water Vapor Transport (kg m⁻¹ s⁻¹) during the event.
- `duration_hours` (float): Duration of the event in hours.
- `landfall_lat` (float): Latitude of primary landfall point (degrees North).
- `landfall_lon` (float): Longitude of primary landfall point (degrees East, converted to West for analysis).
- `region_flag` (bool): Boolean flag indicating if the event intersected the target West Coast NA region (120°W-125°W).

**Derived Attributes (for analysis)**:
- `month` (int): Month index (1-12) of the event start.
- `year` (int): Year of the event start.
- `monthly_iwvt_sum` (float): Sum of peak IWVT for all events in a given month (used as AR intensity proxy).
- `monthly_event_count` (int): Number of AR events in a given month.

---

### 1.2 Gravity Anomaly
Represents a processed gravity measurement derived from GRACE-FO mascon solutions.

**Source**: GRACE-FO L2 Mascon Solutions (via PO.DAAC)
**Granularity**: Grid cell / Regional average
**Temporal Resolution**: Monthly means (derived from ~1-month repeat cycles)

**Fields**:
- `grid_id` (str): Unique identifier for the spatial grid cell or region.
- `center_lat` (float): Center latitude of the grid cell/region (degrees North).
- `center_lon` (float): Center longitude of the grid cell/region (degrees East, converted to West for analysis).
- `time_period` (datetime): ISO 8601 month string (e.g., "2018-01-01") representing the averaging window.
- `mascon_solution` (str): Identifier for the specific GRACE-FO mascon solution version used (e.g., "JPL RL06").

**Physical Definition (Frame of Reference)**:
> **Note**: Gravity anomaly refers to geoid height variations at satellite altitude (GRACE-FO L2 mascon solutions), NOT local surface gravitational acceleration. This is a covariant description of mass redistribution effects on the geopotential field at the measurement altitude, distinguishing physical curvature from coordinate artifacts.

**Values**:
- `equiv_water_height` (float): Equivalent Water Height (EWH) in meters. Positive values indicate mass gain (water accumulation), negative indicate mass loss.
- `uncertainty` (float): Estimated uncertainty of the EWH measurement in meters (derived from mascon metadata).
- `degree_1_corrected` (bool): Flag indicating if degree-1 coefficient correction has been applied.
- `c20_replaced` (bool): Flag indicating if C20 coefficient replacement has been applied.
- `smoothed` (bool): Flag indicating if Gaussian smoothing has been applied.

**Derived Attributes (for analysis)**:
- `month` (int): Month index (1-12).
- `year` (int): Year.
- `regional_mean_ewh` (float): Mean EWH across the target West Coast NA region for the given month.

---

### 1.3 Correlation Result
Represents the statistical outcome of the correlation analysis between AR intensity and Gravity Anomalies.

**Source**: Computed via `04_correlation.py` and `05_bootstrap_correction.py`
**Granularity**: Analysis run (specific lag, region, and method)

**Fields**:
- `analysis_id` (str): Unique identifier for the analysis run.
- `region_type` (str): "target" (West Coast NA) or "control" (non-AR active region).
- `lag_months` (int): Time lag applied to AR data relative to gravity data (0 to 3 months).
- `method` (str): Statistical method used (e.g., "pearson", "spearman", "ar1_residuals").
- `n_observations` (int): Effective number of observations used (after autocorrelation correction).
- `correlation_coefficient` (float): Pearson correlation coefficient (r).
- `p_value` (float): Raw p-value from the correlation test.
- `p_value_fdr` (float): FDR-corrected p-value for multiple comparisons.
- `significant_fdr` (bool): Boolean flag indicating if `p_value_fdr < 0.05` (informational only, not a success criterion).
- `bootstrap_ci_lower` (float): Lower bound of the 95% bootstrap confidence interval.
- `bootstrap_ci_upper` (float): Upper bound of the 95% bootstrap confidence interval.
- `signal_to_noise_ratio` (float): Ratio of |correlation_coefficient| to the noise floor derived from control regions.
- `timestamp` (datetime): ISO 8601 timestamp when the analysis was performed.

**Constraints**:
- `n_observations` must be > 0.
- `correlation_coefficient` must be in [-1, 1].
- `p_value` must be in [0, 1].
- `bootstrap_ci_lower` <= `correlation_coefficient` <= `bootstrap_ci_upper`.

---

## 2. Data Flow & Transformation Rules

### 2.1 Ingestion -> Preprocessing
- **AR Events**: Raw event list -> Filtered by region (120°W-125°W) -> Aggregated to `monthly_iwvt_sum`.
- **Gravity**: Raw mascon grid -> Degree-1 correction -> C20 replacement -> Gaussian smoothing -> Regional mean aggregation.

### 2.2 Preprocessing -> Merge
- **Join Key**: `year` and `month`.
- **Alignment**: AR intensity (monthly sum) aligned with Gravity Anomaly (monthly mean) for the same calendar month.
- **Exclusion**: Months with zero AR events are excluded from correlation calculation (as per `02_preprocessing.py` logic).

### 2.3 Merge -> Analysis
- **Input**: `merged_monthly.csv` (contains `year`, `month`, `iwvt_sum`, `regional_mean_ewh`).
- **Pre-whitening**: AR(1) model applied to both series; residuals used for correlation to correct for autocorrelation.
- **Lagging**: AR series shifted by 0, 1, 2, 3 months relative to Gravity series.

## 3. Schema Compliance

All CSV outputs must strictly adhere to the schemas defined in:
- `contracts/dataset.schema.yaml` (for `merged_monthly.csv`)
- `contracts/output.schema.yaml` (for `correlation_results.json`)

Any deviation in column names, types, or missing required fields will cause the pipeline to fail validation.