# Data Model: Atmospheric River Gravity Correlation

## Entity Definitions

### AR Event

Represents an atmospheric river occurrence with attributes for date, peak intensity (IWV transport), and geographic footprint.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| event_id | string | Unique identifier | Format: `AR-YYYYMMDD-NN` |
| date | date | Event date (YYYY-MM-DD) | ISO 8601 format |
| peak_iwv_transport | float | Peak Integrated Water Vapor Transport (kg/m/s) | ≥ 0 |
| footprint_lat_min | float | Southern boundary latitude (degrees) | -90 to 90 |
| footprint_lat_max | float | Northern boundary latitude (degrees) | -90 to 90 |
| footprint_lon_min | float | Western boundary longitude (degrees) | -180 to 180 |
| footprint_lon_max | float | Eastern boundary longitude (degrees) | -180 to 180 |
| region_overlap | boolean | Overlaps with study region (35°N-50°N, 120°W-125°W) | true/false |

### Gravity Anomaly

Represents monthly GRACE-FO mascon values for the study region with attributes for date, geoid height anomaly at satellite altitude, and uncertainty.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| anomaly_id | string | Unique identifier | Format: `GRACE-YYYYMM` |
| date | date | Month (YYYY-MM-01) | ISO 8601 format |
| geoid_anomaly_m | float | Geoid height anomaly at satellite altitude (meters) | Any real value |
| uncertainty_m | float | Measurement uncertainty (meters) | > 0 |
| region_lat_min | float | Study region southern boundary | 35.0 |
| region_lat_max | float | Study region northern boundary | 50.0 |
| region_lon_min | float | Study region western boundary | -125.0 |
| region_lon_max | float | Study region eastern boundary | -120.0 |
| completeness | float | Data completeness for month | 0.0 to 1.0 |

### Correlation Result

Represents the statistical output with attributes for lag, correlation coefficient, p-values, confidence intervals, and significance flag.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| result_id | string | Unique identifier | Format: `CORR-LAG{N}` |
| lag_months | integer | Lag in months | 0, 1, 2, or 3 |
| correlation_coefficient | float | Pearson r | -1.0 to 1.0 |
| raw_p_value | float | Uncorrected p-value | 0.0 to 1.0 |
| corrected_p_value | float | Bonferroni/FDR corrected p-value | 0.0 to 1.0 |
| ci_lower | float | Bootstrap 95% CI lower bound | -1.0 to 1.0 |
| ci_upper | float | Bootstrap 95% CI upper bound | -1.0 to 1.0 |
| significant | boolean | Significance flag (p < 0.05 corrected) | true/false |
| region_type | string | Target or control region | "target" or "control" |

## Data Flow

```
Raw Data (GRACE-FO, NOAA) 
    ↓ [Phase 0: Ingestion]
Merged Monthly CSV (data/processed/merged_monthly.csv)
    ↓ [Phase 1: Preprocessing]
Preprocessed Time Series
    ↓ [Phase 2: Analysis]
Correlation Results (JSON/CSV)
    ↓ [Phase 3: Sensitivity]
Sensitivity Report (PDF/HTML)
    ↓ [Phase 4: Visualization]
Plot Files (PNG) + Final Report
```

## File Schemas

### Input: GRACE-FO Mascon (raw)

| Column | Type | Description |
|--------|------|-------------|
| date | date | Observation date |
| lat | float | Latitude |
| lon | float | Longitude |
| geoid_anomaly | float | Geoid height anomaly (m) |
| uncertainty | float | Measurement uncertainty (m) |

### Input: NOAA AR Catalog (raw)

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | AR event date |
| peak_iwv | float | Peak IWV transport (kg/m/s) |
| lat_min | float | Footprint southern boundary |
| lat_max | float | Footprint northern boundary |
| lon_min | float | Footprint western boundary |
| lon_max | float | Footprint eastern boundary |

### Output: Merged Monthly CSV

| Column | Type | Description |
|--------|------|-------------|
| month | date | YYYY-MM |
| grace_anomaly_m | float | Mean gravity anomaly over region |
| grace_uncertainty_m | float | Mean uncertainty over region |
| ar_intensity_iwv | float | Total IWV transport from AR events |
| ar_event_count | integer | Number of AR events in month |
| completeness | float | Data completeness (0.0-1.0) |

### Output: Correlation Results

| Column | Type | Description |
|--------|------|-------------|
| lag_months | integer | Lag window |
| correlation | float | Pearson r |
| raw_p | float | Uncorrected p-value |
| corrected_p | float | Corrected p-value |
| ci_lower | float | Bootstrap CI lower |
| ci_upper | float | Bootstrap CI upper |
| significant | boolean | Significance flag |
