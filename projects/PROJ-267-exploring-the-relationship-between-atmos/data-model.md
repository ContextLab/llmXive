# Data Model: Atmospheric River Gravity Correlation

This document defines the core entities, attributes, and relationships used throughout the `PROJ-267-exploring-the-relationship-between-atmos` pipeline. These definitions align with the requirements in `plan.md` (Phase 1 output) and serve as the contract for data ingestion, preprocessing, and analysis tasks.

## 1. Entity: AR Event (Atmospheric River Event)

**Description**: A discrete atmospheric river event identified in the NOAA CPC Atmospheric River Catalog. Represents a specific instance of moisture transport associated with a weather system.

**Source**: NOAA CPC Atmospheric River Catalog (ERDDAP endpoint).

**Attributes**:
- `event_id`: (string) Unique identifier for the AR event (e.g., from the catalog).
- `start_time`: (datetime) UTC timestamp when the event began.
- `end_time`: (datetime) UTC timestamp when the event ended.
- `intensity`: (float) Integrated Water Vapor Transport (IWVT) or a derived intensity metric (e.g., max IWVT during the event). Units: kg m⁻¹ s⁻¹.
- `duration`: (float) Duration of the event in hours (derived from start/end times).
- `region`: (string) Geographic region classification (e.g., "West Coast NA").
- `latitude_range`: (tuple of float) Latitude bounds of the event's impact (e.g., (35.0, 50.0)).
- `longitude_range`: (tuple of float) Longitude bounds of the event's impact (e.g., (-125.0, -120.0)).

**Derived Aggregations (Monthly)**:
- `month`: (datetime) First day of the month (YYYY-MM-01).
- `monthly_ar_count`: (int) Number of distinct AR events occurring within the month.
- `monthly_mean_intensity`: (float) Mean intensity of all AR events in the month.
- `monthly_max_intensity`: (float) Maximum intensity observed among all events in the month.

## 2. Entity: Gravity Anomaly (GRACE-FO Mascon)

**Description**: A monthly gravity field anomaly measurement derived from GRACE-FO L2 Mascon RL06 solutions. Represents changes in the Earth's gravitational field (geoid height variations) due to mass redistribution (e.g., water storage changes).

**Source**: PO.DAAC CMR search API for GRACE-FO L2 Mascon RL06.

**Attributes**:
- `timestamp`: (datetime) First day of the month (YYYY-MM-01).
- `region`: (string) Geographic region identifier (e.g., "West Coast NA").
- `lat_min`, `lat_max`: (float) Latitude bounds of the region (e.g., 35.0, 50.0).
- `lon_min`, `lon_max`: (float) Longitude bounds of the region (e.g., -125.0, -120.0).
- `mascon_value`: (float) Raw mascon solution value (Equivalent Water Height or Geoid Height) before preprocessing. Units: mm or m (consistent with source).
- `uncertainty`: (float) Estimated uncertainty of the mascon value (1-sigma).
- `degree_1_corrected`: (bool) Flag indicating if degree-1 coefficient correction has been applied.
- `c20_replaced`: (bool) Flag indicating if the C20 coefficient has been replaced with the satellite laser ranging (SLR) value.
- `smoothed`: (bool) Flag indicating if 300 km Gaussian smoothing has been applied.

**Preprocessing Steps (Applied to Raw Data)**:
1. **Degree-1 Correction**: Apply center-of-mass corrections (degree-1 coefficients) to account for the motion of the center of mass of the Earth system.
2. **C20 Replacement**: Replace the GRACE/GRACE-FO C20 coefficient with values from Satellite Laser Ranging (SLR) to improve accuracy.
3. **Gaussian Smoothing**: Apply a 300 km Gaussian filter to reduce north-south striping noise.
4. **Monthly Aggregation**: Average the processed mascon values over the defined region for each month.

## 3. Entity: Correlation Result

**Description**: The statistical outcome of analyzing the relationship between AR Event intensity and Gravity Anomaly over a specified lag window.

**Source**: Computed via `code/03_correlation.py` and `code/04_bootstrap_correction.py`.

**Attributes**:
- `lag_months`: (int) Time lag in months between the AR event and the gravity anomaly (0, 1, 2, or 3).
- `region_type`: (string) Classification of the region analyzed ("target" for West Coast NA, "control" for a non-AR region).
- `pearson_r`: (float) Pearson correlation coefficient.
- `p_value`: (float) Two-tailed p-value from the Pearson test.
- `n_samples`: (int) Number of paired data points used in the calculation.
- `confidence_interval_lower`: (float) Lower bound of the 95% bootstrap confidence interval for `pearson_r`.
- `confidence_interval_upper`: (float) Upper bound of the 95% bootstrap confidence interval for `pearson_r`.
- `fdr_corrected_p`: (float) False Discovery Rate (FDR) corrected p-value for multiple comparisons.
- `significance_flag`: (bool) Informational flag indicating if `p_value < 0.05` (not a pre-specified success criterion).
- `noise_floor_sigma`: (float) Signal magnitude relative to the GRACE-FO measurement noise floor (in units of σ).
- `signal_above_noise`: (bool) Flag indicating if the signal magnitude exceeds the 3σ threshold.

**Relationships**:
- Links `AR Event` (aggregated monthly) and `Gravity Anomaly` (aggregated monthly) via a time-lagged join.
- Aggregates results across multiple lag windows and region types.

## 4. Data Flow & Schema Contracts

The pipeline enforces strict schema contracts defined in `contracts/`:

1. **Raw Data**: Downloaded from sources into `data/raw/` with checksums.
2. **Preprocessed Data**:
 - `merged_monthly.csv`: Contains aligned monthly `AR Event` and `Gravity Anomaly` data.
 - Schema: `contracts/dataset.schema.yaml`.
3. **Analysis Output**:
 - `correlation_results.json` (or similar): Contains `Correlation Result` entities.
 - Schema: `contracts/output.schema.yaml`.

## 5. Notes on Physical Interpretation

- **Reference Frame**: The "Gravity Anomaly" refers to geoid height variations at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration. This distinction is critical for physical interpretation (per Constitution Principle II and reviewer feedback).
- **Causality**: All statistical findings are reported as associational. Causal language (e.g., "causes", "effect", "driven by") is explicitly avoided in generated reports to prevent misinterpretation of temporal correlations as causal mechanisms.