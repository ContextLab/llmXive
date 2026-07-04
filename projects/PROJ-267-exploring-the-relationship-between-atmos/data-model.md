# Data Model: Atmospheric River Gravity Correlation

This document defines the core entities, attributes, and relationships used throughout the
PROJ-267 automated science pipeline. It aligns with the project plan (Phase 1 output) and
the user stories defined in `specs/001-atmospheric-river-gravity/spec.md`.

## 1. Overview

The project investigates the statistical relationship between Atmospheric River (AR) events
and localized gravity anomalies measured by the GRACE-FO satellite mission. The data model
is designed to support the ingestion of raw satellite and meteorological data, the
preprocessing of these signals into monthly aggregates, and the statistical analysis of
their correlation.

## 2. Core Entities

### 2.1. AR Event (Atmospheric River Event)

Represents a single detected atmospheric river event from the NOAA CPC catalog.
This entity is the primary input for the "atmospheric" variable in the correlation study.

| Attribute | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `event_id` | string | Unique identifier for the event (e.g., from NOAA catalog). | NOAA CPC AR Catalog |
| `start_time` | datetime | UTC timestamp of the event start. | NOAA CPC AR Catalog |
| `end_time` | datetime | UTC timestamp of the event end. | NOAA CPC AR Catalog |
| `max_iwvt` | float | Maximum Integrated Water Vapor Transport (kg m⁻¹ s⁻¹) during the event. | NOAA CPC AR Catalog |
| `peak_time` | datetime | Timestamp of maximum IWVT. | Derived |
| `region_code` | string | Identifier for the region where the AR occurred (e.g., `WC_NA` for West Coast NA). | Derived (see Section 3) |
| `latitude` | float | Latitude of the event center (degrees North). | NOAA CPC AR Catalog |
| `longitude` | float | Longitude of the event center (degrees West/East). | NOAA CPC AR Catalog |

**Derived Attributes:**
- `monthly_iwvt`: The sum or mean of `max_iwvt` for all events in a given month within a region. Used for monthly aggregation.

### 2.2. Gravity Anomaly

Represents a processed gravity measurement from the GRACE-FO mission, aggregated to a
specific region and time window. This entity represents the "gravity" variable.

| Attribute | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `anomaly_id` | string | Unique identifier for the anomaly record (e.g., `YYYY-MM_REGION`). | Derived |
| `month` | datetime | The month of the measurement (YYYY-MM-01). | Derived from GRACE-FO |
| `region_code` | string | Region identifier matching the AR Event (e.g., `WC_NA`). | Configuration |
| `mascon_value` | float | Raw mascon solution value (Gaussian smoothed) in mm equivalent water height. | GRACE-FO RL06 |
| `c20_corrected` | boolean | Flag indicating if the C20 coefficient was replaced per GRACE-FO standards. | Processing Flag |
| `degree1_corrected` | boolean | Flag indicating if degree-1 coefficients were applied. | Processing Flag |
| `smoothing_scale` | float | Spatial smoothing scale applied (e.g., 300 km). | Configuration |
| `uncertainty` | float | Estimated measurement uncertainty (mm EWH) based on mascon metadata. | GRACE-FO Metadata |
| `signal_to_noise` | float | Ratio of absolute anomaly value to uncertainty. | Derived |

**Note on Frame of Reference:**
Consistent with the Einstein-simulated review (see `docs/frame-of-reference.md`), these values
represent the geoid height anomaly (or equivalent water height) at the satellite altitude,
processed to remove non-hydrological signals (atmosphere, ocean, tides) to isolate the
terrestrial water storage change.

### 2.3. Correlation Result

Represents the outcome of the statistical analysis between the AR Event aggregates and
Gravity Anomalies. This entity is the final output of the analysis pipeline.

| Attribute | Type | Description | Source |
|:--- |:--- |:--- |:--- |
| `result_id` | string | Unique identifier for the analysis result. | Derived |
| `region_type` | string | Type of region analyzed (e.g., `target`, `control`). | Configuration |
| `region_code` | string | The specific region code analyzed. | Configuration |
| `lag_months` | int | Time lag applied to the AR data relative to gravity data (0 to 3). | Analysis Parameter |
| `pearson_r` | float | Pearson correlation coefficient. | `scipy.stats.pearsonr` |
| `p_value` | float | Two-tailed p-value for the correlation. | `scipy.stats.pearsonr` |
| `p_corrected` | float | P-value after Bonferroni correction for multiple comparisons. | `code/05_bootstrap_correction.py` |
| `is_significant` | boolean | True if `p_corrected` < 0.05 (per SC-002). | Derived |
| `n_observations` | int | Number of data points (months) used in the calculation. | Derived |
| `n_eff` | float | Effective sample size after autocorrelation correction (Newey-West). | `code/04_correlation.py` |
| `ci_lower` | float | Lower bound of the 95% bootstrap confidence interval. | `code/05_bootstrap_correction.py` |
| `ci_upper` | float | Upper bound of the 95% bootstrap confidence interval. | `code/05_bootstrap_correction.py` |
| `methodology` | string | Description of the statistical method used (e.g., "Pearson with AR(1) pre-whitening"). | Configuration |

## 3. Geographic Regions

The project focuses on specific geographic zones to ensure signal coherence.

- **WC_NA (West Coast North America)**:
 - Latitude: 35°N to 50°N
 - Longitude: 120°W to 125°W (approximate coastal strip)
 - Purpose: Target region for AR activity and gravity anomaly correlation.

- **Control Regions**:
 - Selected areas with minimal AR activity but similar climatic conditions to distinguish
 AR-specific signals from global noise or large-scale climate oscillations.
 - Examples: Interior North America, specific Pacific Ocean patches.

## 4. Data Flow and Relationships

1. **Ingestion**: Raw `AR Event` data is fetched from NOAA CPC; raw `Gravity Anomaly`
 data is fetched from GRACE-FO.
2. **Preprocessing**:
 - `AR Event` records are aggregated into monthly bins (`monthly_iwvt`).
 - `Gravity Anomaly` records are corrected (C20, Degree-1) and smoothed.
3. **Merge**: Preprocessed monthly data for a specific `region_code` is joined on `month`.
4. **Analysis**: The merged dataset is used to compute `Correlation Result` entities
 across different `lag_months` and `region_type` values.

## 5. Schema Validation

All CSV outputs must conform to the schemas defined in:
- `contracts/dataset.schema.yaml` (for merged monthly data)
- `contracts/output.schema.yaml` (for correlation results)

These schemas enforce data types, required fields, and value ranges (e.g., no NaN in
primary columns).