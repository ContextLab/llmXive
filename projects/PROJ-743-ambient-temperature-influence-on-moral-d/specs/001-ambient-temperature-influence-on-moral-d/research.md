# Research: Ambient Temperature Influence on Moral Decision Speed

## Executive Summary

This research plan investigates the hypothesis that higher ambient temperatures are associated with faster moral decision-making times, potentially driven by increased physiological arousal (System 1 processing). The study leverages the Moral Machine dataset, merging it with historical land-based temperature data (NOAA GHCN-Daily or ERA5-Land) to create a geospatially and temporally precise dataset. The primary analysis uses a Linear Mixed-Effects Model (LMM) if repeated measures exist, or a Generalized Estimating Equation (GEE) with clustered standard errors if participants only complete one batch. The model controls for participant demographics, dilemma complexity, and cultural region. Robustness checks address potential confounds (indoor/outdoor, measurement error) and non-linearity.

## Dataset Strategy

The analysis relies on two primary datasets. The Moral Machine dataset provides the behavioral outcomes (response times, decisions, demographics), while land-based historical temperature data provides the ambient temperature predictor.

| Dataset | Role | Source / Loader | Verification Status |
|:--- |:--- |:--- |:--- |
| **Moral Machine** | Primary behavioral data (outcomes, covariates, location). | **Verified**: Harvard Dataverse (https://dataverse.harvard.edu/dataset.xhtml?persistentId=) | **Verified**: Canonical source confirmed. |
| **NOAA GHCN-Daily / ERA5-Land** | Ambient temperature predictor (land-based). | **Verified**: NOAA GHCN-Daily (via `nctoolkit` or `xarray`) or ERA5-Land via HuggingFace (`) | **Verified**: Land-based coverage confirmed. |

**Critical Gap Analysis**:
- **Moral Machine Granularity**: The plan includes a verification step to check if the dataset contains precise GPS coordinates or only administrative regions (country/city). If only administrative regions are available, the matching logic will aggregate temperature data to the same level (e.g., daily average per city) rather than attempting a 100km nearest-neighbor join on individual coordinates.
- **Data Structure**: The plan includes a validation step to determine if participants completed multiple dilemmas (repeated measures) or a single batch. This dictates whether LMM (random intercepts) or GEE (clustered SEs) is used.

**Dataset Variable Fit**:
- **Required Variables**: `latitude` (or city/country), `timestamp`, `response_time`, `age`, `gender`, `dilemma_id`, `choice`.
- **Temperature Variables**: `station_id` (or grid point), `timestamp`, `temperature_celsius`.
- **Fit Assessment**: The Moral Machine dataset contains location data (GPS or administrative). The temperature dataset contains land-based observations. A spatial/temporal join is feasible.
- **Risk**: If the Moral Machine dataset lacks precise timestamps (e.g., only date provided), matching to hourly temperature data will be impossible. The plan will use daily averages in this case.

## Methodology

### 1. Data Ingestion and Cleaning (FR-001, FR-002, FR-009, FR-010)
- **Ingestion**: Load Moral Machine CSV and Temperature Parquet/NetCDF.
- **Filtering**:
 - Remove records with missing `latitude`/`longitude` (or administrative region).
 - Remove records with `response_time` < 100ms or > 3 SD from the median (Empirical Outlier Detection) to avoid truncating valid behavioral data.
 - Flag records where the nearest station/grid point is > 100km away (low confidence match).
 - Interpolate missing temperature values if gap ≤ 2 hours; otherwise exclude.
- **Matching**: Perform a spatial join to find the nearest station/grid point, then a temporal join to extract the temperature at the closest hour (or daily average if timestamps are coarse).
- **Output**: `data/processed/merged_dataset.parquet`.

### 2. Feature Engineering
- **Log Transformation**: Apply `log(response_time)` to normalize the distribution (US-2).
- **Covariates**:
 - `dilemma_complexity`: Derived from static dilemma attributes (e.g., absolute difference in lives at stake, or conflict magnitude). This avoids tautological relationships with response time.
 - `time_of_day`: Extracted from timestamp (categorical: morning, afternoon, evening).
 - `indoor_proxy`: If metadata is available, create a proxy; otherwise, flag as limitation (FR-012).
- **Temperature Metrics**:
 - `temp_raw`: Hourly/Daily temperature.
 - `temp_ma3`: 3-hour moving average (robustness check).

### 3. Statistical Modeling (FR-003, FR-004, FR-005, FR-011, FR-013)
- **Data Structure Validation**: First, check if `participant_id` has multiple records.
 - **If Repeated Measures**: Fit Linear Mixed-Effects Model (LMM).
 - **If Independent**: Fit Generalized Estimating Equation (GEE) with clustered standard errors by `participant_id`.
- **Primary Model**:
 - **Dependent Variable**: `log_response_time`.
 - **Fixed Effects**: `temperature_celsius`, `age`, `gender`, `dilemma_complexity`, `time_of_day`.
 - **Random Effects (LMM only)**: `(1 | participant_id)`, `(1 | cultural_region)`.
 - **Non-linearity**: Include `temperature_celsius^2` (quadratic term) to test for inverted-U effects (FR-013).
- **Null Model**: Same structure but without `temperature_celsius`.
- **Inference**:
 - Likelihood-ratio test (LRT) or Wald test comparing Full vs. Null model (FR-005).
 - P-values for fixed effects (SC-002) using Satterthwaite or Kenward-Roger approximations to address anti-conservatism.
- **Diagnostics**:
 - QQ-plot of residuals.
 - Residuals vs. Fitted plot.
 - Kolmogorov-Smirnov test for normality (SC-005).

### 4. Robustness and Sensitivity Analysis (FR-006, FR-007, FR-008, FR-012)
- **Threshold Sensitivity**: Sweep the temperature outlier threshold (e.g., 2 SD, 3 SD, 4 SD) and plot the variation in the temperature coefficient (SC-003).
- **Metric Sensitivity**: Compare results using `temp_raw` vs. `temp_ma3`.
- **Indoor/Outdoor Confound**: Explicitly state that temperature is a 'noisy proxy' for the immediate environment. The estimated effect is likely attenuated (biased toward zero). Do not claim to quantify this noise without a valid instrument.
- **Multiple Comparisons**: Apply Bonferroni or False Discovery Rate (FDR) correction if multiple hypothesis tests are run.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since we are testing a primary hypothesis (temperature effect) and several robustness checks, we will apply FDR correction to the set of robustness p-values to control the family-wise error rate.
- **Power Justification**: The Moral Machine dataset is large. However, the effective sample size for the mixed model depends on the number of unique participants and regions. We will report the effective degrees of freedom. If power is low for specific subgroups, we will acknowledge this limitation.
- **Causal Inference**: The study is **observational**. We **cannot** claim causality. The plan explicitly frames results as "associations" or "correlations" (Assumption: "Any observed association... is correlational").
- **Measurement Validity**: The temperature data is a proxy for the participant's immediate thermal environment. The "indoor/outdoor" confound is a known limitation (FR-012). We acknowledge that the estimated effect is likely attenuated due to this noise.
- **Collinearity**: `dilemma_complexity` and `response_time` might be definitionally related. We will check Variance Inflation Factors (VIF) and report collinearity if VIF > 5. We will not claim independent effects if predictors are highly collinear.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - **Sampling**: If the full merged dataset exceeds 6 GB, we will sample [deferred] of records (stratified by region) for the primary model. The full dataset will be used only for descriptive statistics if memory permits.
 - **Library**: `statsmodels` (CPU-optimized) for LMM/GEE. No GPU required.
 - **Runtime**: Estimated < 2 hours for ingestion and modeling on sampled data.
 - **Memory**: Dataframes will be processed in chunks if necessary. `parquet` format used for efficient I/O.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Moral Machine Granularity** | High: GPS coordinates may be missing. | Script checks for GPS; if missing, switches to administrative-level aggregation (city/country) for temperature matching. |
| **NOAA Station Distance > 100km** | High: Temperature proxy is invalid. | Flag records; exclude from primary analysis; report percentage of excluded records. |
| **Model Convergence Failure** | Medium: No results. | Try alternative optimizers (`bfgs`, `lbfgs`); simplify random effects structure; switch to GEE if LMM fails. |
| **Memory Overflow** | High: Job timeout. | Implement chunked processing; sample [deferred] of data; use `float32` instead of `float64`. |