# Feature Specification: Evaluating Calibration of Predictive Intervals in Time Series Forecasting

**Feature Branch**: `[001-calibration-evaluation]`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Evaluating Calibration of Predictive Intervals in Time Series Forecasting"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Evaluation Pipeline (Priority: P1)

As a researcher, I want to ingest the M4 dataset, fit multiple forecasting models, generate prediction intervals, and compute empirical coverage rates so that I can establish a baseline assessment of model calibration.

**Why this priority**: This is the foundational capability; without accurate interval generation and coverage calculation, no analysis is possible. It delivers the primary research value.

**Independent Test**: Can be fully tested by running the pipeline on a subset of 10 series and verifying that the output CSV contains observed coverage rates for [deferred] and [deferred] intervals that match manual calculation on those 10 series.

**Acceptance Scenarios**:

1. **Given** the M4 dataset is accessible, **When** the pipeline processes a sample of 100 time series, **Then** the output includes empirical coverage rates for every series at horizons h=1 to 12.
2. **Given** a fitted model, **When** prediction intervals are generated, **Then** the intervals correspond exactly to the nominal [deferred] and [deferred] external target levels defined in the configuration.
3. **Given** the compute environment limits, **When** the pipeline runs on a sample of 100 series, **Then** it completes within 6 hours using only CPU resources.
4. **Given** the pipeline configuration, **When** the sensitivity analysis runs, **Then** the system reports coverage rates for absolute deviation thresholds of 0.01, 0.05, and 0.1.
5. **Given** multiple models and horizons, **When** statistical significance is reported, **Then** the results include p-values adjusted for multiplicity using the Benjamini-Hochberg FDR method.
6. **Given** the final report, **When** findings are presented, **Then** all performance comparisons are framed strictly as associational observations, avoiding causal claims about model superiority.

---

### User Story 2 - Stratified Analysis (Priority: P2)

As a researcher, I want to group calibration results by series characteristics (seasonality, trend strength, frequency) so that I can identify systematic patterns in mis-calibration.

**Why this priority**: Aggregated results may hide critical failures in specific sub-populations (e.g., seasonal series); this adds necessary diagnostic depth.

**Independent Test**: Can be tested by running the pipeline on a pre-labeled subset containing both seasonal and non-seasonal series and verifying the output groups results correctly by metadata tags.

**Acceptance Scenarios**:

1. **Given** the dataset includes metadata tags for seasonality, **When** the analysis runs, **Then** results are aggregated into at least two distinct groups (seasonal vs. non-seasonal).
2. **Given** a specific subgroup (e.g., high trend strength), **When** results are queried, **Then** the average coverage deviation is reported for that subgroup specifically.

---

### User Story 3 - Recalibration & Comparison (Priority: P3)

As a researcher, I want to apply conformal prediction recalibration methods to the baseline forecasts and compare the new coverage rates against the original ones so that I can quantify potential improvements.

**Why this priority**: This validates the practical utility of the findings by demonstrating a mitigation strategy, but depends on the baseline pipeline (US-1) being complete.

**Independent Test**: Can be tested by taking a fixed set of baseline forecasts, applying one recalibration method, and verifying the new coverage rates shift toward the nominal target.

**Acceptance Scenarios**:

1. **Given** baseline forecasts exist, **When** adaptive conformal prediction is applied, **Then** the recalibrated intervals show a coverage rate closer to the nominal target than the baseline.
2. **Given** multiple models, **When** recalibration is applied, **Then** the improvement is reported per model to allow comparison of recalibration efficacy.

---

### Edge Cases

- What happens when a time series is too short to split into training and test sets? (System MUST skip the series and log a warning).
- How does system handle models that fail to converge on specific series? (System MUST catch the exception, record the failure, and continue processing other series without crashing).
- What happens when the M4 dataset metadata is missing specific fields (e.g., frequency)? (System MUST skip the series and log a warning; trend strength is derived, not missing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the M4 competition dataset from the official repository, retaining at least 1,000 representative time series to ensure compute feasibility. (See US-1)
- **FR-002**: System MUST fit ARIMA, ETS, Prophet, and LightGBM models. For LightGBM, the system MUST use a quantile regression objective with alpha=0.1 and alpha=0.05 to generate valid prediction intervals. (See US-1)
- **FR-003**: System MUST generate predictive intervals at [deferred] and [deferred] nominal external target levels for horizons h = 1 to 12. (See US-1)
- **FR-004**: System MUST calculate empirical coverage as the proportion of test points falling inside the predicted interval for each series and model. (See US-1)
- **FR-005**: System MUST implement a stratification logic that groups results by seasonality (yes/no) and trend strength (high/low), where trend strength is derived via STL decomposition using only the training split and classified as 'high' if the variance ratio > 0.5. (See US-2)
- **FR-006**: System MUST implement adaptive conformal prediction recalibration as a post-processing step on baseline forecasts. (See US-3)
- **FR-007**: System MUST apply multiplicity correction using the Benjamini-Hochberg False Discovery Rate (FDR) method when reporting statistical significance across multiple models and horizons. (See US-1)
- **FR-008**: System MUST perform a sensitivity analysis on the calibration threshold by sweeping the absolute deviation between empirical and nominal coverage values across a range of small magnitudes. (See US-1)
- **FR-009**: System MUST frame all performance findings as associational comparisons between models, not causal claims about model superiority. (See US-1)
- **FR-010**: System MUST validate that the M4 metadata contains the required variables for stratification (specifically 'seasonality' and 'frequency') before proceeding with analysis. (See US-2)

### Key Entities *(include if feature involves data)*

- **TimeSeries**: Represents a single row from the M4 dataset, including historical observations and metadata (frequency, seasonality).
- **ForecastResult**: Represents the output of a model, including point forecasts and lower/upper bounds for the specified confidence levels.
- **CalibrationMetric**: Aggregated statistics (coverage, width, interval score) associated with a specific model and horizon.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Total pipeline runtime is measured against the GitHub Actions free-tier limit. (See US-1)
- **SC-002**: Empirical coverage deviation is measured against the nominal [deferred]/95% external target, with a target threshold of ≤2% absolute deviation. (See US-1)
- **SC-003**: Statistical significance is measured against the corrected alpha level after multiplicity adjustment. (See US-1)
- **SC-004**: Sensitivity analysis results are measured by reporting coverage rates at small threshold deviations. (See US-1)
- **SC-005**: Sample size adequacy is measured by ensuring the selected series represent ≥90% of the original M4 frequency distribution. (See US-1)

## Assumptions

- **Compute Feasibility**: The analysis assumes a representative subset of the M dataset is sufficient, as fitting multiple models on the full dataset exceeds the computational time constraint.
- **Dataset Availability**: The M4 competition dataset is assumed to be accessible via the official GitHub repository without authentication barriers.
- **Metadata Validity**: It is assumed that M4 metadata contains 'seasonality' and 'frequency' fields. It is further assumed that 'trend strength' is NOT explicitly in the metadata and must be derived via STL decomposition on the training split only, calculating the variance ratio of the trend component to the total variance.
- **Model Availability**: It is assumed that standard Python/R libraries (`statsmodels`, `forecast`, `prophet`, `lightgbm`) are available in the CI environment without requiring heavy compilation steps.
- **Inference Framing**: Findings are assumed to be correlational regarding model performance, as no random assignment of series to models occurs.
- **Threshold Justification**: The ≤2% deviation threshold is based on community standards for acceptable calibration in forecasting benchmarks, subject to the sensitivity sweep defined in FR-008.
- **No GPU**: The analysis assumes no access to GPU accelerators; all methods must run on CPU in default precision.
- **Sensitivity Analysis Justification**: The sensitivity sweep (FR-008) is required to validate that the ≤2% deviation target is robust and not an artifact of a single arbitrary threshold choice.
- **Multiplicity Correction Justification**: The Benjamini-Hochberg FDR method (FR-007) is required because testing multiple hypotheses (multiple models × multiple horizons) without correction guarantees false positives; FDR is the standard for this scale in forecasting literature (e.g., M4/M5 papers). Note: While forecast errors are autocorrelated, FDR is robust to positive dependence; the limitation of assuming independence is acknowledged.