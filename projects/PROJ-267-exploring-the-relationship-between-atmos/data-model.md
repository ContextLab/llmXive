# Data Model: Atmospheric River Gravity Correlation

This document defines the core entities and data structures used throughout the
`PROJ-267-exploring-the-relationship-between-atmos` pipeline. It serves as the
canonical reference for data ingestion, preprocessing, analysis, and visualization
tasks (US1, US2, US3).

## 1. Entity Definitions

### 1.1 Atmospheric River Event (AR Event)

Represents a single detected atmospheric river event from the NOAA CPC Atmospheric
River Catalog. This entity captures the spatiotemporal extent and intensity metrics
of the event.

**Source**: NOAA CPC Atmospheric River Catalog (ERDDAP endpoint)
**Granularity**: Event-level (can span multiple days)

**Attributes**:
- `event_id` (string): Unique identifier for the AR event.
- `start_time` (datetime): UTC timestamp of event onset.
- `end_time` (datetime): UTC timestamp of event termination.
- `max_integrated_water_vapor_transport` (float): Maximum Integrated Water Vapor
 Transport (IVT) magnitude observed during the event, in kg m⁻¹ s⁻¹.
- `max_ivt_latitude` (float): Latitude of the maximum IVT point (degrees N).
- `max_ivt_longitude` (float): Longitude of the maximum IVT point (degrees E).
- `duration_hours` (integer): Total duration of the event in hours.
- `region` (string): Geographic region classification (e.g., "West Coast NA").
- `source_version` (string): Version string of the NOAA dataset used.

**Derived/Aggregated Attributes (Monthly)**:
- `month` (string): ISO 8601 month string (YYYY-MM).
- `ar_count` (integer): Number of AR events occurring within the month.
- `mean_monthly_ivt` (float): Mean of `max_integrated_water_vapor_transport` for all
 events in the month.
- `total_ivt_sum` (float): Sum of IVT magnitudes for the month (proxy for total
 moisture flux).

---

### 1.2 Gravity Anomaly (GRACE-FO Mascon)

Represents a gravity field anomaly measurement derived from GRACE-FO Level 2 mascon
solutions. **Crucial Distinction**: This anomaly refers to geoid height variations
at satellite altitude (approx. 500 km), not surface gravitational acceleration.
This distinction is required to satisfy covariant descriptions of the gravitational
field and avoid coordinate artifacts (per Einstein-simulated review).

**Source**: NASA PO.DAAC GRACE-FO Level 2 Mascon Solutions
**Granularity**: Monthly, spatially resolved (mascon grid cells)

**Attributes**:
- `month` (string): ISO 8601 month string (YYYY-MM).
- `region_id` (string): Identifier for the spatial region (e.g., "WC_NA_120W_125W").
- `mascon_id` (string): Unique identifier for the specific mascon grid cell.
- `latitude` (float): Center latitude of the mascon (degrees N).
- `longitude` (float): Center longitude of the mascon (degrees E).
- `equivalent_water_height` (float): Equivalent Water Height (EWH) anomaly in mm.
 Positive values indicate mass gain (water accumulation); negative indicate loss.
- `uncertainty` (float): Estimated standard error of the mascon solution in mm.
- `c20_corrected` (boolean): Flag indicating if C20 coefficient replacement was applied.
- `degree_1_corrected` (boolean): Flag indicating if degree-1 coefficient correction was applied.
- `source_version` (string): Version string of the GRACE-FO dataset used.

**Derived/Aggregated Attributes (Regional Monthly Mean)**:
- `mean_regional_ewh` (float): Spatial mean of `equivalent_water_height` across all
 mascons in the target region for the given month.
- `std_regional_ewh` (float): Spatial standard deviation of EWH in the region.
- `coverage_fraction` (float): Fraction of the region covered by valid mascon data.

---

### 1.3 Correlation Result

Represents the statistical output of the correlation analysis between AR intensity
and Gravity Anomalies. This entity encapsulates the relationship metrics, including
lag analysis and bootstrap confidence intervals.

**Source**: Computed via `04_correlation.py` and `05_bootstrap_correction.py`
**Granularity**: Lag-window specific (e.g., lag 0, lag 1, etc.)

**Attributes**:
- `analysis_id` (string): Unique identifier for the analysis run.
- `region_type` (string): "target" (West Coast NA) or "control" (non-AR region).
- `lag_months` (integer): Time lag in months (0 = synchronous, 1 = AR leads gravity, etc.).
- `pearson_correlation` (float): Pearson correlation coefficient (r).
- `p_value` (float): Two-tailed p-value for the correlation.
- `effective_sample_size` (integer): Sample size adjusted for autocorrelation (n_eff).
- `bootstrap_ci_lower` (float): Lower bound of the 95% bootstrap confidence interval.
- `bootstrap_ci_upper` (float): Upper bound of the 95% bootstrap confidence interval.
- `fdr_corrected_p` (float): P-value after False Discovery Rate correction.
- `significance_flag` (boolean): True if `fdr_corrected_p` < 0.05 (informational only,
 not a pre-specified success criterion per Constitution Principle VII).
- `noise_floor_sigma` (float): Signal magnitude expressed in units of GRACE-FO
 measurement noise (σ).
- `methodology_notes` (string): Text description of pre-whitening (AR(1) residuals)
 and frame-of-reference (geoid height at satellite altitude).

---

## 2. Data Flow & Transformation Rules

1. **Ingestion**: Raw AR events and GRACE-FO mascons are fetched and stored in
 `data/raw/`. No transformation is applied at this stage.
2. **Preprocessing**:
 - **AR**: Aggregated to monthly resolution per region. Events with zero
 intensity or missing timestamps are excluded.
 - **Gravity**: Degree-1 and C20 corrections applied. Gaussian smoothing applied.
 Spatial averaging performed over the defined West Coast NA region.
 - **Alignment**: Both datasets are aligned to a common monthly index (YYYY-MM).
3. **Merging**: Preprocessed datasets are merged on `month` and `region_id` to
 produce `data/processed/merged_monthly.csv`.
4. **Analysis**: Correlation is computed on the merged data, applying AR(1)
 pre-whitening to residuals before calculating Pearson `r`.
5. **Output**: Final results are stored in `data/processed/correlation_results.json`
 and visualized in `output/`.

## 3. Constraints & Validations

- **Temporal Alignment**: Months with missing data in either dataset are logged
 and skipped in correlation calculations (no imputation).
- **Zero-Event Months**: Months with zero AR events in the target region are
 excluded from the correlation analysis to prevent skewing.
- **Frame of Reference**: All gravity anomaly values must be explicitly documented
 as geoid height variations at satellite altitude to distinguish from surface
 gravity artifacts.
- **Causal Language**: All derived reports must avoid causal framing (e.g., "causes",
 "impact") and strictly describe associational findings.