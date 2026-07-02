# Research: Ambient Temperature Influence on Moral Decision Speed

## Problem Statement

This research investigates whether ambient temperature influences the speed of moral decision-making. The hypothesis is derived from the "System 1" (intuitive) vs. "System 2" (deliberative) framework: higher temperatures may induce physiological arousal, potentially accelerating intuitive responses (faster reaction times) or, conversely, causing cognitive overload and slowing deliberation. The study leverages the Moral Machine dataset, which contains millions of moral dilemma choices, and merges it with high-resolution historical weather data (ERA5) to test this association while controlling for demographic and situational covariates.

**CRITICAL DATA GAP**: The verified ERA source provided (`era5_1982_1.h5`) covers the year 1982. The Moral Machine dataset was launched in the mids and contains data from the subsequent years. There is **NO TEMPORAL OVERLAP**. The project cannot proceed without a verified source for ERA5 data covering the 2016-2019 period. This is a blocking flaw.

## Dataset Strategy

### Primary Dataset: Moral Machine
- **Description**: A large-scale dataset of moral dilemma choices collected from the "Moral Machine" platform. Contains participant ID, location (lat/long), timestamp, dilemma attributes, response time, and choice.
- **Usage**: Source of the dependent variable (response time) and independent variables (dilemma type, choice).
- **Verified Source**: The specific URL for the Moral Machine dataset is **not** listed in the "Verified datasets" block provided for this project. The plan assumes the dataset will be ingested from the canonical source (e.g., `moral-machine-data` on GitHub or a provided CSV) as per the project's data ingestion requirements. *Note: If the source cannot be verified, the ingestion step will fail the "Verified Accuracy" gate.*

### Secondary Dataset: ERA5 Reanalysis
- **Description**: ECMWF's fifth-generation reanalysis of global climate data, providing hourly estimates of atmospheric, land, and ocean variables.
- **Usage**: Source of the primary independent variable (ambient temperature) matched by location and time.
- **Verified Source**: ` (as listed in the project's verified datasets block).
- **Fit Assessment**: The dataset provides hourly temperature data at high spatial resolution.. This is sufficient for matching with the Moral Machine data, provided the Moral Machine data includes precise timestamps and coordinates.
- **Coverage Check**: The provided ERA5 file covers 1982. The Moral Machine dataset (launched ~) contains data from 2016-2019. **CRITICAL MISMATCH**: The verified ERA5 file (1982) does not temporally overlap with the Moral Machine dataset (2016+).
 - **Resolution**: The plan **MUST** halt. The implementation will not proceed until a verified source for ERA5 data covering 2016-2019 is added to the verified datasets block. If no such source exists, the project is unfeasible.

### Data Matching Strategy
1. **Temporal Alignment**: Match Moral Machine timestamps (UTC) to the nearest ERA5 hourly record (only if 2016-2019 data is available).
2. **Spatial Alignment**: Match Moral Machine coordinates to the nearest ERA5 grid cell.
3. **Quality Control**: Exclude records where:
 - Distance to nearest ERA5 grid > 100km.
 - Time gap > 2 hours (no interpolation).
 - Temperature out of range (-50°C to +60°C).

## Statistical Methodology

### Primary Model: Linear Mixed-Effects Model (LMM)
- **Outcome**: Log-transformed response time (to address right-skew).
- **Fixed Effects**:
 - `temperature_celsius`: Primary predictor.
 - `temperature_squared`: To test for non-linearity (quadratic term).
 - `dilemma_complexity`: Derived score (static, non-time-based, based on lives/species only to avoid circularity).
 - `time_of_day`: Categorical or circular variable.
 - `choice_type`: "Save many" vs. "Save few" (FR-011).
 - `age`: Participant age (if available) (FR-004).
 - `gender`: Participant gender (if available) (FR-004).
- **Random Effects**:
 - `(1 | participant_id)`: Accounts for individual baseline speed.
 - `(1 | cultural_region)`: Accounts for regional cultural differences.
- **Autocorrelation Handling**: Test for temporal autocorrelation in residuals. If present, use cluster-robust standard errors or an AR(1) correlation structure.
- **Rationale**: LMM is robust to unbalanced data and handles the hierarchical structure of the data (multiple responses per participant) better than OLS.

### Secondary Models & Robustness
1. **Alternative Temperature Metrics**: Use 3-hour moving average of temperature to smooth noise.
2. **Indoor/Outdoor Proxy**: Stratify by urban/rural classification of coordinates if available; **however**, acknowledge this is a weak proxy. The primary strategy is to report this as a limitation and quantify the potential noise impact via robustness checks (FR-012).
3. **Sensitivity Analysis**: Sweep outlier thresholds (e.g., 2SD, 3SD, 4SD) to ensure the temperature coefficient is stable.
4. **Non-Linearity Test**: Compare LMM with linear vs. quadratic temperature terms using AIC/BIC.

### Assumptions & Limitations
- **Causality**: The design is observational. Claims will be limited to *associations*. No causal inference will be made regarding temperature causing speed changes.
- **Collinearity**: `dilemma_complexity` and `response_time` must be derived independently to avoid circularity.
- **Power**: The large sample size of Moral Machine should provide high power, but the effective sample size is reduced by the geospatial/temporal matching process.
- **Measurement Validity**: ERA5 is a reanalysis product, not direct measurement. It is a valid proxy for ambient temperature at the grid scale.
- **Indoor/Outdoor Confound**: Urban/rural classification is a poor proxy for the actual thermal environment. The analysis will explicitly report this as a limitation rather than claiming to control for it.

## Feasibility Check (CPU/Runner)
- **Compute**: The LMM (via `statsmodels` or `lme4` equivalent in Python) is computationally intensive. To ensure feasibility on a 2-CPU, 7GB RAM runner:
 - **Subsampling**: A stratified random sample of sufficient size to address memory constraints will be used if the full dataset exceeds memory limits.
 - **Fallback**: If LMM fails to converge, a fixed-effects-only model or GLMM with log-link will be used.
- **Memory**: The merged dataset must be kept under 7 GB RAM. Chunking or sampling is required.
- **Time**: The pipeline (ingest -> merge -> model) is estimated to run within 6 hours on a 2-core runner, provided subsampling is applied.

## Decision Log
- **Dataset Gap**: The verified ERA5 file (1982) does not match the Moral Machine timeframe (2016+). The plan is **BLOCKED** until a verified source for the correct period is identified.
- **Model Choice**: LMM selected over GLMM for simplicity and speed on CPU, unless log-transformation fails (then GLMM with log-link).
- **Confounder Handling**: Indoor/outdoor confound addressed by acknowledging the limitation of the urban/rural proxy and quantifying noise via robustness checks.
- **Complexity Derivation**: `dilemma_complexity` must be derived solely from static attributes (lives, species) to avoid circularity with response time.
- **Autocorrelation**: Temporal autocorrelation will be tested; if present, cluster-robust SEs or AR(1) structure will be applied.