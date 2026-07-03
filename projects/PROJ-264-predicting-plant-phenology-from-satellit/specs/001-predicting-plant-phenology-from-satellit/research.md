# Research: Predicting Plant Phenology from Satellite Imagery and Climate Data

## Executive Summary

This research phase validates the feasibility of the proposed data pipeline and modeling approach. It confirms dataset availability, assesses computational constraints, and outlines the statistical methodology for predicting plant phenology.

**Key Methodological Corrections**:
1. **Validation**: Switched from single-site holdout to **Spatial Block Cross-Validation** and **Temporal Holdout** to prevent spatial autocorrelation bias.
2. **Feature Independence**: Implemented **Lagged Feature Windows** (pre-event data only) to prevent data leakage.
3. **Multicollinearity**: Removed `gdd_cumulative` from raw inputs; diagnosed VIF for remaining features.
4. **Exploratory Nature**: Explicitly framed results as exploratory due to small sample size.

## Dataset Strategy

| Dataset | Source URL | Format | Variables Needed | Status |
|---------|------------|--------|------------------|--------|
| **Satellite (Sentinel-2)** | ` (API) | API | NDVI, EVI, Date, Site | **Primary Source** (FR-001). Requires `earthengine.authenticate()`. |
| **Climate (Temp/Precip)** | ` (GHCN) / NASA POWER API | API | Temp, Precip, Solar Radiation | **Primary Source** (FR-002). |
| **Phenology Ground Truth** | ` (Nature's Notebook) | API | Event Date, Species, Site | **Primary Source** (FR-003). |
| **Satellite (Landsat)** | ` | CSV | NDWI, Date | **Unit Test Only**. Used solely to verify parsing logic, NOT for model validation. |
| **EnvironmentalTimeSeries** | *Constructed Pipeline* | CSV | Aligned features | **Gap Identified**: Must be constructed via ingestion pipeline. |

> **Critical Note**:
> - The Landsat dataset is **not** used for validation of the Sentinel-2 pipeline due to resolution/sensor mismatch.
> - The 2000 Afghanistan dataset is **excluded** as it is temporally misaligned with the -2023 research window.
> - All primary validation relies on the GEE API output against Nature's Notebook ground truth.

## Methodological Rationale

### Data Ingestion & Alignment (US-1)
- **Approach**: Use `earthengine-api` to query Sentinel-2 for NDVI/EVI.
- **Temporal Alignment**: Resample to 10-day intervals using linear interpolation for gaps ≤1 interval (FR-008).
- **Cloud Cover**: Filter scenes with >20% cloud cover; exclude sites with insufficient data.
- **Climate Integration**: Fetch daily NOAA/NASA data and aggregate to 10-day means/maxs.
- **Phenology Mapping**: Match ground-truth event dates to the **nearest preceding 10-day satellite window** (Lagged features only).
- **Lagged Feature Window**: Features are extracted from a window *prior* to the event (e.g., Jan-Mar for April budburst) to ensure predictor independence from the outcome.

### Modeling Strategy (US-2)
- **Algorithm**: XGBoost regressor (primary), LightGBM (fallback).
- **Features**: NDVI, EVI, Cumulative Growing Degree Days (GDD - **derived at training time**), Precipitation, Solar Radiation.
- **Multicollinearity Check**: Calculate Variance Inflation Factor (VIF). If VIF > 5 for any pair (e.g., NDVI/EVI), retain only one.
- **Validation**:
 - **Spatial Block Cross-Validation**: K=5 blocks based on geographic clustering.
 - **Temporal Holdout**: Train on early historical data, Test on recent data.
 - **No Conditional Filters**: Generalization error is reported **regardless** of climate distribution shift. Shift magnitude is recorded as a secondary metric.
- **Metrics**: RMSE, MAE, R² (FR-005).
- **Baseline**: Simple linear regression on temperature only (SC-001).
- **Exploratory Note**: Due to small sample size (10-15 sites), results are framed as exploratory with wide confidence intervals.

### Sensitivity & Interpretability (US-3)
- **Hyperparameter Sweep**: Alpha values {0.01, 0.05, 0.1} (FR-006).
- **Feature Importance**: Permutation importance (FR-007) on the **reduced** feature set (after VIF check).
- **Robustness**: Report RMSE variation across sweeps (SC-003).

## Compute Feasibility Assessment

| Component | Resource Estimate | Feasibility on Free Tier (2 CPU, 7GB RAM) |
|-----------|-------------------|------------------------------------------|
| **Data Download** | ~500 MB (compressed) | ✅ Feasible (Network I/O bound) |
| **Preprocessing** | ~2 GB RAM peak | ✅ Feasible (Pandas chunking) |
| **Model Training** | ~1-2 GB RAM, 30-60 min | ✅ Feasible (XGBoost/LightGBM are CPU-optimized) |
| **Sensitivity Analysis** | ~1-2 GB RAM, 15 min | ✅ Feasible (Small sweep set) |
| **Total Runtime** | ~2-3 hours | ✅ Feasible (Well under h limit) |

**Risk Mitigation**:
- **Memory**: Use `pandas` chunking for large files; downsample if necessary.
- **Time**: Limit cross-validation folds to; restrict hyperparameter grid.
- **API Limits**: Implement exponential backoff for API retries.
- **Authentication**: Ensure `earthengine.authenticate()` is called before pipeline start.

## Statistical Rigor Considerations

- **Multiple Comparisons**: Not applicable (single model family, limited sweep).
- **Power Analysis**: Acknowledged limitation; dataset size (a small number of sites) is small. Results framed as **exploratory**.
- **Causal Inference**: Observational study. Claims limited to **associational** relationships. No causal claims made.
- **Collinearity**: Addressed via VIF check and feature selection (removing GDD from raw inputs).
- **Measurement Validity**: Sentinel-2 NDVI/EVI are standard remote sensing indices. Nature's Notebook is the gold standard for ground truth.

## Gaps & Assumptions

- **Gap**: No verified dataset for full 2018-2023 Sentinel-2 time-series. **Action**: Rely on Google Earth Engine API (FR-001).
- **Assumption**: Google Earth Engine API is accessible with standard authentication (`earthengine.authenticate()`).
- **Assumption**: Climate data (NOAA/NASA) is available for all 10-15 sites.
- **Assumption**: Phenology events occur within the 2018-2023 window for all sites.
