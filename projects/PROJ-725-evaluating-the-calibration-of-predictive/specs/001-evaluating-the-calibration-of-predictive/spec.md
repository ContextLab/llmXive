# Feature Specification: Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks

**Feature Branch**: `001-evaluating-the-calibration`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks statistics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Benchmarking Pipeline (Priority: P1)

A researcher needs to download a set of public regression datasets, fit four specific uncertainty quantification methods (Quantile Regression, Bayesian Linear Regression, Gaussian Process Regression, and Split Conformal Prediction), and generate [deferred] prediction intervals to assess their empirical coverage against the nominal target.

**Why this priority**: This is the Minimum Viable Product (MVP). Without the ability to generate intervals and measure their coverage, the research question cannot be answered. All subsequent analyses (heteroscedasticity, training size) depend on this core pipeline.

**Independent Test**: The pipeline can be tested by running it on a single small public dataset (e.g., the Boston Housing dataset with ~500 samples) and verifying that the script outputs a CSV containing the true target, lower bound, upper bound, and a binary "covered" flag for each method, with no runtime errors.

**Acceptance Scenarios**:

1. **Given** a valid URL to a regression dataset from UCI or OpenML, **When** the pipeline executes the download and 70/30 split, **Then** the training and test sets are created with a fixed random seed and the test set size is approximately one-third of the total.
2. **Given** a training set, **When** the four methods are fitted, **Then** each method produces a lower and upper bound for every test sample such that the interval width is non-negative.
3. **Given** the generated intervals and true test targets, **When** the empirical coverage is calculated, **Then** the result is a float between 0.0 and 1.0 representing the proportion of targets falling within their respective intervals.

---

### User Story 2 - Statistical Calibration Assessment (Priority: P2)

A researcher needs to determine if the observed coverage significantly deviates from the nominal [deferred] target and quantify the efficiency of the intervals using the Interval Score, including corrections for multiple hypothesis testing.

**Why this priority**: This adds the statistical rigor required to answer "How well calibrated are..." beyond simple observation. It transforms raw coverage numbers into statistically defensible conclusions.

**Independent Test**: The assessment can be tested by feeding the P1 output (coverage and intervals) into the analysis module and verifying that a p-value is generated for the binomial test and that the interval score is calculated without GPU usage.

**Acceptance Scenarios**:

1. **Given** the empirical coverage rate from a method on a dataset, **When** the binomial test is performed against the null hypothesis of 0.90, **Then** a p-value is returned, and the system flags the result as "mis-calibrated" if p < 0.05. This test is performed separately for the global marginal coverage and for each variance-stratified bin to distinguish between global and conditional calibration.
2. **Given** multiple methods tested across multiple datasets, **When** the pairwise comparison test is applied to compare coverage deviations, **Then** the system applies a permutation test (exact or Monte Carlo with a sufficient number of iterations) to the resulting differences, as n=10 is too small for Wilcoxon assumptions.
3. **Given** the predicted intervals and true values, **When** the Interval Score is computed, **Then** the score reflects both the sharpness (width) and calibration (penalty for misses) according to the Gneiting & Raftery (2007) definition.

---

### User Story 3 - Heteroscedasticity and Sensitivity Analysis (Priority: P3)

A researcher needs to investigate whether calibration failures are concentrated in high-variance regions and determine if the conclusions are robust to small changes in the decision threshold used to define "mis-calibration."

**Why this priority**: This addresses the "Expected results" nuance regarding heteroscedastic regions and provides the required methodological robustness (sensitivity analysis) to defend the findings against threshold-cherry-picking.

**Independent Test**: The analysis can be tested by running the sub-analysis on a single dataset with known heteroscedastic noise and verifying that coverage rates differ significantly between low-variance and high-variance bins.

**Acceptance Scenarios**:

1. **Given** a dataset with estimated residual variance, **When** test points are stratified into low, medium, and high variance bins, **Then** the empirical coverage is reported separately for each bin.
2. **Given** a nominal deviation threshold of ±2%, **When** the sensitivity analysis is run, **Then** the system recalculates the "mis-calibration" count for thresholds of ±1%, ±2%, and ±3% and reports the variation in the headline rate.
3. **Given** the training data, **When** the training size is subsampled to [deferred], [deferred], and [deferred] of the training data, **Then** the coverage trends are plotted or tabulated to show the effect of data volume on calibration stability.

### Edge Cases

- What happens if a dataset has a limited number of samples, making the [deferred] test split too small for reliable binomial testing? The system must skip the binomial significance test for that specific dataset and flag it as "insufficient sample size."
- How does the system handle datasets with missing values in the target variable? The system must drop rows with missing targets before splitting, logging the count of dropped rows.
- What happens if the Gaussian Process exact inference exceeds the 7 GB RAM limit on a specific dataset? The system must catch the memory error, log a warning, and skip that specific method for that dataset, proceeding to the next method.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess a set of public regression datasets from UCI/OpenML, ensuring all required variables (features and target) are present, with a 70/30 train/test split using a fixed seed (See US-1).
- **FR-002**: System MUST implement four uncertainty quantification methods: Quantile Regression (linear + GBT), Bayesian Linear Regression, Gaussian Process Regression (RBF kernel), and Split Conformal Prediction (See US-1).
- **FR-003**: System MUST generate two-sided prediction intervals at a nominal confidence level for all test samples using the fitted models (See US-1).
- **FR-004**: System MUST calculate empirical coverage, average interval width, and the proper Interval Score for every method-dataset pair (See US-2).
- **FR-005**: System MUST perform a binomial test against the 0.90 null hypothesis for global and conditional coverage, and a permutation test with a sufficient number of iterations for pairwise method comparisons to ensure validity at n=10 (See US-2).
- **FR-006**: System MUST train a variance model (e.g., GAMLSS or heteroscedastic regression) on the training set to predict residual variance for test points, then stratify test points by predicted variance (low/medium/high) and report coverage per bin to assess heteroscedasticity (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis sweeping the mis-calibration threshold from ±1% to ±3% in 1% increments and report the resulting change in mis-calibration rates (See US-3).
- **FR-008**: System MUST execute all computations using CPU-only methods (no CUDA/GPU) and fit within 7 GB RAM and 14 GB disk constraints (See Assumptions).

### Key Entities

- **Dataset**: A public regression table containing numeric/categorical features and a continuous target variable.
- **Prediction Interval**: A pair of bounds (lower, upper) generated by a specific method for a specific test sample.
- **Calibration Metric**: A derived statistic (e.g., coverage rate, interval score, p-value) summarizing the performance of a method on a dataset.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Empirical coverage rates are measured against the nominal [deferred] target to determine the magnitude of over- or under-coverage (See US-2).
- **SC-002**: Interval scores are measured against the theoretical minimum (perfect calibration + zero width) to quantify efficiency trade-offs (See US-2).
- **SC-003**: Statistical significance of calibration deviations is measured against a binomial distribution null hypothesis with family-wise error rate correction (See US-2).
- **SC-004**: Heteroscedasticity impact is measured by the difference in coverage rates between low-variance and high-variance bins (See US-3).
- **SC-005**: Sensitivity of conclusions is measured by the variation in mis-calibration counts across the ±1%, ±2%, and ±3% threshold sweep (See US-3).
- **SC-006**: Conditional calibration validity is measured by performing separate binomial tests for each variance-stratified bin to ensure coverage holds locally, not just globally (See US-2).

## Assumptions

- The 10 selected UCI/OpenML datasets contain sufficient sample sizes (≥ 200 total) to allow a 70/30 split where the test set supports a meaningful binomial test.
- The "free CPU" GitHub Actions runner (2 cores, ~7 GB RAM) is sufficient to run exact Gaussian Process inference on datasets with ≤ 10,000 samples if data is pre-filtered or subsampled if necessary.
- The "mis-calibration" threshold of ±2% (observed vs. nominal coverage) is a defensible community-standard default for this scale of study, as no specific value was mandated in the idea.
- All cited datasets are accessible without authentication or complex scraping logic; direct URL downloads are assumed to be stable.
- The Python environment on the runner includes `scikit-learn`, `statsmodels`, and `GPyTorch` (or `sklearn.gaussian_process` for CPU-only GP) with compatible versions.
- If a specific method (e.g., GP) fails due to memory constraints on a large dataset, the study will proceed with the remaining successful methods for that dataset, and the failure will be logged as a limitation.