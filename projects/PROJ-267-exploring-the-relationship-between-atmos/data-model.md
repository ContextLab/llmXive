# Data Model: Atmospheric River Gravity Correlation

This document defines the core data entities used in the `PROJ-267` pipeline, aligning with the requirements specified in `plan.md` Phase 1 output and the user stories for data ingestion, correlation analysis, and visualization.

## 1. Entity Definitions

### 1.1 AR Event (Atmospheric River Event)
Represents a single detected atmospheric river event from the NOAA CPC Atmospheric River Catalog. This entity captures the meteorological forcing component of the study.

**Source**: NOAA CPC Atmospheric River Catalog (via `code/01_data_ingestion.py`)

**Attributes**:
- `event_id`: (string) Unique identifier for the AR event (e.g., "AR_2020_001").
- `start_time`: (datetime) UTC timestamp of event onset.
- `end_time`: (datetime) UTC timestamp of event termination.
- `intensity_class`: (string) Classification of the event (e.g., "AR Cat 1", "AR Cat 2", etc., or "Strong", "Weak").
- `max_iwv_transport`: (float) Maximum Integrated Water Vapor Transport observed during the event, in kg/(m·s).
- `peak_date`: (date) The date on which the maximum IWV transport occurred.
- `region`: (string) Geographic region where the event was detected (e.g., "West Coast NA").
- `source_url`: (string) Reference URL to the original catalog entry.

**Derived Aggregates (Monthly)**:
- `month`: (string) ISO 8601 month string (e.g., "2020-01").
- `monthly_event_count`: (integer) Number of distinct AR events occurring in this month within the target region.
- `monthly_max_iwv`: (float) Maximum daily IWV transport value observed in the month.
- `monthly_cumulative_iwv`: (float) Sum of daily peak IWV values for all events in the month.

---

### 1.2 Gravity Anomaly
Represents the processed mass variation data derived from GRACE-FO mascon solutions, corrected for degree-1 and C20 coefficients, and smoothed. This entity captures the geophysical response component.

**Source**: GRACE-FO Level-3 Mascon Solutions (via `code/02_preprocessing.py`)

**Attributes**:
- `grid_cell_id`: (string) Unique identifier for the spatial grid cell (e.g., "lat_40_lon_-122").
- `latitude`: (float) Center latitude of the grid cell in degrees.
- `longitude`: (float) Center longitude of the grid cell in degrees.
- `date`: (date) Date of the monthly solution.
- `equivalent_water_height`: (float) Equivalent Water Height (EWH) in meters, representing the mass anomaly relative to a reference mean.
- `uncertainty`: (float) Estimated uncertainty of the measurement (1-sigma) in meters.
- `c20_corrected`: (boolean) Flag indicating if C20 coefficient replacement was applied.
- `degree_1_corrected`: (boolean) Flag indicating if degree-1 coefficient correction was applied.

**Derived Aggregates (Regional Monthly)**:
- `month`: (string) ISO 8601 month string.
- `region_mean_ewh`: (float) Area-weighted mean EWH across the target region (35°N-50°N, 120°W-125°W) for the month.
- `region_std_ewh`: (float) Standard deviation of EWH across the region.
- `anomaly_flag`: (boolean) Indicator if the monthly mean exceeds 3σ of the regional noise floor (per FR-004).

---

### 1.3 Correlation Result
Represents the statistical output of the analysis comparing AR intensity metrics against Gravity Anomaly metrics. This entity is the final product of the statistical pipeline (User Story 2).

**Source**: Statistical analysis scripts (`code/04_correlation.py`, `code/05_bootstrap_correction.py`)

**Attributes**:
- `analysis_id`: (string) Unique identifier for the correlation analysis run.
- `region_type`: (string) Type of region analyzed ("target" or "control").
- `lag_months`: (integer) Time lag in months applied to the AR data relative to the gravity data (0, 1, 2, or 3).
- `correlation_coefficient`: (float) Pearson correlation coefficient (r).
- `p_value`: (float) P-value from the t-test on the correlation coefficient.
- `p_value_corrected`: (float) P-value after multiple-comparison correction (e.g., Bonferroni).
- `is_significant`: (boolean) True if `p_value_corrected` < 0.05 (per SC-002).
- `bootstrap_ci_lower`: (float) Lower bound of the 95% bootstrap confidence interval for r.
- `bootstrap_ci_upper`: (float) Upper bound of the 95% bootstrap confidence interval for r.
- `effective_sample_size`: (float) Calculated effective sample size (n_eff) after autocorrelation correction.
- `noise_floor_threshold`: (float) The 3σ noise floor value used for signal validation (meters).
- `signal_magnitude`: (float) Observed signal magnitude relative to the noise floor.
- `null_result_flag`: (boolean) True if the correlation coefficient is < 0.1 or if the signal is indistinguishable from noise.

---

## 2. Data Flow & Relationships

1. **Ingestion**: `AR Event` and `Gravity Anomaly` records are fetched from external sources and stored in `data/raw/`.
2. **Preprocessing**: Raw records are aggregated into monthly time-series:
 - `AR Event` → `Monthly AR Summary` (contains `monthly_max_iwv`).
 - `Gravity Anomaly` → `Monthly Gravity Summary` (contains `region_mean_ewh`).
3. **Merge**: The monthly summaries are joined on `month` to form the `merged_monthly.csv` dataset.
4. **Analysis**: The merged dataset is used to compute `Correlation Result` entries for various lag windows and region types.

## 3. Schema Validation

All data artifacts must conform to the schemas defined in:
- `contracts/dataset.schema.yaml` (for `merged_monthly.csv`)
- `contracts/output.schema.yaml` (for `Correlation Result` outputs)

Validation is enforced by `code/03_merge_output.py` and `code/05_bootstrap_correction.py`.