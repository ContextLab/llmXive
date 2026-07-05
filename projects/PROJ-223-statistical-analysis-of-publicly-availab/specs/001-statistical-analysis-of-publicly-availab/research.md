# Research: Statistical Analysis of Publicly Available Traffic Accident Data

## Dataset Strategy

The analysis relies on two primary datasets: the Fatality Analysis Reporting System (FARS) for accident details and NOAA GHCN-Daily for weather observations. The following verified sources are used exclusively.

| Dataset | Purpose | Verified URL | Access Method | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **FARS (2021)** | Accident severity, location, time, vehicle type | ` | Direct HTTP Download | Official NHTSA source. Contains `SEVERITY`, `LAT`, `LON`, `HOUR`, `DAY`, `ROAD_TYPE`, `VEH_TYPE`. |
| **NOAA GHCN-Daily** | Precipitation, visibility, temperature | ` | Direct HTTP Download | Contains daily weather summaries. **Schema Check**: Script verifies presence of `VIS` (visibility), `PRCP` (precipitation), `TAVG` (temperature). If missing, script halts with error. |
| **NOAA Buoy** | Supplemental weather (if needed) | ` | Direct HTTP Download | Backup source for coastal accidents. |

**Dataset-Variable Fit Assessment**:
The spec requires specific variables: `severity`, `precipitation`, `visibility`, `temperature`, `hour`, `day_of_week`, `road_type`, `vehicle_type`.
- **FARS Source**: The verified URL (`data.nhtsa.gov/FARS/FARS2021CSV.zip`) is the official NHTSA source. The ingestion script will validate that the downloaded CSV contains the required columns (`SEVERITY`, `LAT`, `LON`, etc.) before merging.
- **NOAA Source**: The HuggingFace split is used as a verified proxy. The ingestion script includes a schema validation step to ensure the specific artifact contains the `VIS`, `PRCP`, and `TAVG` columns required for the `WeatherObservation` entity. If these columns are missing, the script will log a critical error and halt, preventing analysis on an insufficient dataset.

**Data Volume & Sampling Strategy**:
- **Constraint**: GitHub Actions free tier (7GB RAM).
- **Strategy**: If the merged dataset exceeds 5GB, the pipeline will apply stratified sampling to reduce the dataset to a manageable size while preserving the distribution of the outcome variable (severity). The sampling ratio will be logged.

## Statistical Methodology

### Primary Model: Ordinal Logistic Regression (OLR)
- **Rationale**: The outcome variable (Severity) is ordinal (Property < Injury < Fatality). OLR respects this ordering and provides odds ratios for the cumulative probability of being in a higher severity category.
- **Assumptions**:
 1. **Proportional Odds**: The effect of predictors is constant across all thresholds.
 2. **Independence**: Observations are independent (addressed via Cluster-Robust Standard Errors).
 3. **No Multicollinearity**: Predictors are not highly correlated.
- **Implementation**: `statsmodels.miscmodels.ordinal_model.OrderedModel`.

### Fallback Model: Multinomial Logistic Regression (MLR) or Penalized GLM
- **Trigger 1 (Proportional Odds Violation)**: If the Brant test or Likelihood Ratio Test p < 0.05, switch to MLR (`statsmodels.discrete.discrete_model.MNLogit`).
- **Trigger 2 (Multicollinearity)**: If VIF > 5, switch to a Generalized Linear Model (GLM) with a logit link and L2 regularization (`fit_regularized`) or a robust estimator to handle collinearity, as `OrderedModel` does not natively support L2 penalties.
- **Implementation**: `statsmodels.discrete.discrete_model.MNLogit` or `statsmodels.genmod.generalized_linear_model.GLM`.

### Missing Data Handling
- **Method**: Multiple Imputation by Chained Equations (MICE) using `sklearn.impute.IterativeImputer`.
- **Rationale**: Simple deletion (Complete Case Analysis) introduces severe selection bias if missing weather data correlates with severe storms (the event of interest). MICE preserves the distribution of extreme events.
- **Implementation**: Impute `precipitation`, `visibility`, and `temperature` based on other weather and accident variables.

### Diagnostics & Remediation
- **Multicollinearity**: Variance Inflation Factor (VIF) calculated for all predictors.
 - **Threshold**: VIF > 5.
 - **Action**: Switch to Penalized GLM or Robust Estimator.
- **Clustering**: Cluster-Robust Standard Errors (CRSE) calculated, clustering by `county_id` (or nearest proxy) and `date`.
- **Model Fit**: Likelihood Ratio Test (LRT) comparing the full model to an intercept-only model. McFadden's Pseudo R-squared reported.
- **Sensitivity Analysis**: Instead of post-hoc power, calculate the **Minimum Detectable Effect (MDE)**. Given the final sample size N and alpha=0.05, what is the smallest Odds Ratio detectable with [deferred] power? Report MDE. If MDE < 1.5, the study is considered sufficiently powered for the target effect.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|:--- |:--- |:--- |
| **Use `statsmodels` over `scikit-learn`** | `statsmodels` provides detailed statistical inference (p-values, confidence intervals, diagnostics) required for academic rigor. `scikit-learn` focuses on prediction. | `scikit-learn` lacks built-in OLR and detailed diagnostic outputs. |
| **CPU-only execution** | GitHub Actions free tier does not support GPU. | GPU-based training (e.g., PyTorch) is infeasible. |
| **Fallback to MLR/Regularized GLM** | Ensures the pipeline produces results even if OLR assumptions fail or multicollinearity is high. | Failing the pipeline on assumption violation would block all results. |
| **Stratified Sampling** | Maintains class balance in the outcome variable when reducing data size. | Random sampling might distort the rare "Fatality" class distribution. |
| **MICE for Missing Data** | Prevents selection bias from non-random missing weather data. | Complete Case Analysis would bias results against severe weather conditions. |
| **Sensitivity Analysis (MDE)** | Provides meaningful information about study power without the tautology of post-hoc power analysis. | Post-hoc power analysis is statistically invalid for validating study design. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Mismatch** | The verified FARS URL points to non-traffic data. | Pipeline halts with clear error; logs missing columns. (Resolved by using official NHTSA URL). |
| **NOAA Schema Mismatch** | The HuggingFace split lacks required columns. | Schema verification step in `01_data_ingestion.py` checks for `VIS`, `PRCP`, `TAVG`. |
| **Non-Convergence** | Model fails to converge on full dataset. | Use robust optimization settings; fallback to MLR or Penalized GLM. |
| **Memory Overflow** | Merged dataset > 7GB RAM. | Implement chunked processing and stratified sampling. |
| **Missing Weather Data** | No weather data matches accident timestamps. | Log warning; proceed with available data; report sample reduction. |
