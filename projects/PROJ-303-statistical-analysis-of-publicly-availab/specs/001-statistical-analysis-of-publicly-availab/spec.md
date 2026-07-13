# Feature Specification: Statistical Analysis of Publicly Available Weather Data for Extreme Event Prediction

**Feature Branch**: `001-extreme-weather-spatial-analysis`  
**Created**: 2026-07-07  
**Status**: Draft  
**Input**: User description: "How does spatial dependence structure the tail behavior of localized extreme weather events, and what is the predictive gain of modeling this dependence over independent station assumptions?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Extreme Event Definition (Priority: P1)

The system MUST ingest NOAA GHCN-Daily data for a dense sub-region (e.g., Northeast USA), handle missing values via station-specific imputation, and define extreme events using a peaks-over-threshold approach (a high percentile calculated strictly on the 2000–2015 training set).

**Why this priority**: Without a clean, standardized dataset of defined extreme events, no modeling or comparison can occur. This is the foundational data layer required for all subsequent analysis.

**Independent Test**: Can be fully tested by running the data pipeline on the 2000–2015 training split and verifying that the output contains a time-series of exceedance indicators and magnitudes for 90–110 stations with <1% missing data after imputation. The test MUST verify that stations with >15% total missing data OR a contiguous gap >30 days are EXCLUDED, and that the 95th percentile threshold is calculated ONLY from the training data and applied fixed to the test set.

**Acceptance Scenarios**:

1. **Given** a raw NOAA GHCN-Daily CSV file for the Northeast USA, **When** the ingestion script processes it, **Then** stations with >15% total missing data OR a contiguous gap >30 days are excluded, and remaining gaps are filled via linear interpolation.
2. **Given** a station's daily rainfall history, **When** the extreme event module runs, **Then** days exceeding the 95th percentile (calculated strictly on the 2000–2015 training data) are flagged as exceedances with their corresponding magnitude values.
3. **Given** the processed dataset, **When** a summary statistic is requested, **Then** the system reports the count of exceedances per station and the average magnitude of those exceedances, confirming data integrity.

---

### User Story 2 - Baseline vs. Spatial Model Comparison (Priority: P2)

The system MUST fit two models: a baseline independent Generalized Pareto Distribution (GPD) for each station and a Brown-Resnick max-stable process (with Matérn covariance) that accounts for tail dependence. The system MUST then compute prediction errors (Brier score, RMSE) on a held-out test set (2019–2020), ensuring the Brier score is derived from probabilistic exceedance predictions.

**Why this priority**: This is the core research question. The value lies in quantifying the "predictive gain" of spatial modeling. This story delivers the primary comparative metric.

**Independent Test**: Can be fully tested by executing the model training and evaluation pipeline on the 2000–2015 training and 2019–2020 test splits, producing a JSON report with Brier scores and RMSE for both the independent and spatial models. The test MUST verify that if the spatial model fitting exceeds a predefined time threshold, the system logs a warning, falls back to the independent GPD model, and reports the fallback event.

**Acceptance Scenarios**:

1. **Given** the preprocessed extreme event data, **When** the independent GPD model is fitted, **Then** each station's marginal distribution is estimated without considering spatial correlation.
2. **Given** the same data, **When** the Brown-Resnick max-stable process is fitted, **Then** the model estimates the tail dependence structure (e.g., via variograms or copulas) across the station network.
3. **Given** the test set (2019–2020), **When** both models predict regional extremes, **Then** the system calculates and outputs the Brier score (based on probabilistic exceedance) and RMSE for both models, clearly distinguishing the independent baseline from the spatial approach.

---

### User Story 3 - Cross-Validation and Diagnostic Visualization (Priority: P3)

The system MUST perform "leave-one-station-out" cross-validation to assess prediction at unseen locations and generate diagnostic plots (variograms of extremes, QQ-plots, regional exceedance probability maps).

**Why this priority**: This validates the robustness of the spatial model's generalization capabilities and provides the visual evidence required for the research paper's results section.

**Independent Test**: Can be fully tested by running the cross-validation loop on the full dataset and verifying that the output includes a set of diagnostic plots and a summary of the cross-validation error reduction compared to the baseline. The test MUST verify that the 6-hour compute limit is monitored and that the fallback to the independent model is triggered if the limit is approached, logging the event.

**Acceptance Scenarios**:

1. **Given** the trained spatial model, **When** the leave-one-station-out loop executes, **Then** the model predicts extremes for a held-out station using only data from its neighbors.
2. **Given** the model residuals, **When** diagnostic plots are generated, **Then** a variogram of extremes and a QQ-plot for marginal fits are produced to visually assess model fit.
3. **Given** the test period data, **When** the system maps regional exceedance probabilities, **Then** a spatial map is generated showing the probability of extreme events occurring across the region, highlighting areas of high tail dependence.

### Edge Cases

- What happens when a station has a long contiguous block of missing data (e.g., >30 days) that linear interpolation cannot reasonably fill? -> The system MUST flag this station for exclusion (regardless of total missing percentage) and log the event.
- How does the system handle the "edge effect" where stations at the geographic boundary of the sub-region have fewer neighbors for the spatial model? -> The system MUST use a nearest-neighbor approach or boundary correction to ensure all stations are included in the spatial dependency estimation.
- What happens if the spatial model fitting fails to converge within the 6-hour CPU limit? -> The system MUST fallback to the independent GPD model for that specific iteration and log a warning, ensuring the pipeline completes.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and parse NOAA GHCN-Daily data for a dense sub-region (e.g., Northeast USA) containing 90–110 stations, covering the period 2000–2020. (See US-1)
- **FR-002**: The system MUST implement a peaks-over-threshold method to identify extreme events, using a 95th percentile threshold calculated strictly on the 2000–2015 training set to account for climate trends without data leakage. (See US-1)
- **FR-003**: The system MUST fit an independent Generalized Pareto Distribution (GPD) model for each station's marginal extremes using `scipy.stats` or `pyextremes`. (See US-2)
- **FR-004**: The system MUST fit a Brown-Resnick max-stable process (with Matérn covariance) that explicitly captures tail dependence structure across the station network. (See US-2)
- **FR-005**: The system MUST evaluate both models on a held-out test set (recent years) using Brier scores (derived from probabilistic exceedance predictions) and RMSE for intensity prediction. (See US-2)
- **FR-006**: The system MUST perform a leave-one-station-out cross-validation to assess the spatial model's predictive performance at unseen locations. (See US-3)
- **FR-007**: The system MUST generate diagnostic visualizations including variograms of extremes, QQ-plots for marginal fits, and maps of predicted regional exceedance probabilities. (See US-3)
- **FR-008**: The system MUST enforce a hard compute limit of 6 hours on 2 CPU cores and <7GB RAM. The system MUST monitor elapsed time at regular intervals; if the estimated remaining time exceeds a significant threshold before the 6-hour limit, or if the hard limit is reached, the system MUST trigger subsampling or fallback to the independent GPD model and log the event. (See US-2)

### Key Entities

- **Station**: Represents a weather monitoring location with attributes: `station_id`, `latitude`, `longitude`, `elevation`, `time_series` (daily values).
- **ExtremeEvent**: Represents a specific day where a threshold is exceeded, with attributes: `station_id`, `date`, `magnitude`, `threshold_value`.
- **ModelFit**: Represents the result of a statistical model, with attributes: `model_type` (independent/spatial), `parameters`, `convergence_status`, `computation_time`.
- **EvaluationMetric**: Represents a performance measure, with attributes: `metric_name` (Brier, RMSE), `value`, `model_type`, `test_period`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The reduction in Brier score for binary exceedance prediction is measured against the independent GPD baseline to quantify the predictive gain of spatial modeling. (See US-2)
- **SC-002**: The reduction in RMSE for intensity prediction is measured against the independent GPD baseline to assess accuracy improvements in magnitude estimation. (See US-2)
- **SC-003**: The empirical coverage of 95% confidence intervals for regional sums is measured against the nominal level to validate the uncertainty quantification of the spatial model, where intervals are constructed via block bootstrap with block size equal to the estimated correlation length. (See US-2)
- **SC-004**: The mean squared error of the leave-one-station-out cross-validation is measured against the independent model's cross-validation error to assess generalization to unseen locations. (See US-3)
- **SC-005**: The total wall-clock execution time of the full analysis pipeline is measured against the 6-hour limit to ensure CPU-only feasibility. (See US-2)

## Assumptions

- The NOAA GHCN-Daily dataset contains sufficient station density in the Northeast USA (or equivalent sub-region) to support spatial dependence modeling with a representative sample of stations.
- The "95th percentile" threshold is a defensible community standard for defining "extreme" events in this context; sensitivity analysis will sweep this threshold over {90th, 95th, 99th} percentiles to verify robustness.
- The spatial dependence structure is stationary or piecewise stationary within the selected sub-region, allowing for the application of standard max-stable or spatial GPD models.
- The computational cost of fitting the Brown-Resnick max-stable process on the full 2000–2015 dataset will fit within the 6-hour CPU limit; if not, the system will subsample the time series (e.g., every 3rd day) to ensure feasibility.
- The `SpatialExtremes` R package (or a Python equivalent like `spatial-extremes` in `scipy`/`pymc`) is available and compatible with the free-tier GitHub Actions environment (CPU-only, no GPU).
- Missing data in the NOAA dataset is primarily random or short-duration gaps, making linear interpolation a valid imputation strategy for the majority of stations.