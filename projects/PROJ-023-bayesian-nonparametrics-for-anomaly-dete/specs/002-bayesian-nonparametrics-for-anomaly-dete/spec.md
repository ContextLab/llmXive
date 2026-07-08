# Feature Specification: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Feature Branch**: `001-bayesian-nonparametrics-anomaly-detection`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Bayesian Nonparametrics for Anomaly Detection in Time Series"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Bayesian Inference Pipeline (Priority: P1)

The researcher needs to ingest univariate time series data, inject synthetic anomalies with known ground truth, and run a Gaussian Process regression with Sparse Variational Inference to generate anomaly probability scores.

**Why this priority**: This is the primary research value proposition. Without the core Bayesian nonparametric model functioning and producing scores, the comparison with baselines and the investigation of shift detectability are impossible.

**Independent Test**: Can be fully tested by loading a single preprocessed time series window, running the inference script, and verifying that the output file contains anomaly probability scores for every time step while staying within 7GB memory and 6-hour time limits.

**Acceptance Scenarios**:

1. **Given** a normalized univariate time series window with injected synthetic anomalies, **When** the Bayesian model runs Sparse Variational Inference, **Then** it outputs a CSV file containing anomaly probability scores for each time step.
2. **Given** memory constraints of <7GB and a 6-hour job limit, **When** the model initializes and runs for 1000 inference steps, **Then** the process completes successfully without triggering OOM errors or timeout.
3. **Given** a dataset with abrupt variance changes, **When** the model processes the data, **Then** it produces higher anomaly scores at the injected variance shift points compared to stable regions.

---

### User Story 2 - Baseline Comparison Engine (Priority: P2)

The researcher needs to execute traditional Statistical Process Control (SPC) charts (Shewhart, CUSUM) and a lightweight Variational Auto-Encoder (VAE) on the same data to establish a performance baseline.

**Why this priority**: The research question relies on comparing the Bayesian approach against standard benchmarks to determine relative sensitivity. This enables the calculation of whether the Bayesian method offers a distinct advantage for specific shift types.

**Independent Test**: Can be fully tested by running the baseline algorithms on a held-out test set with known anomalies and generating F1-scores independently of the Bayesian model results.

**Acceptance Scenarios**:

1. **Given** a test dataset with known synthetic anomalies, **When** the Shewhart control chart is applied with a threshold of 3 standard deviations, **Then** it identifies anomalies based on control limits and outputs binary flags.
2. **Given** a test dataset, **When** the VAE (CPU mode) is applied with a reconstruction error threshold, **Then** it reconstructs the input and flags deviations exceeding the threshold as anomalies.
3. **Given** the same input data as Story 1, **When** the CUSUM procedure is executed, **Then** it detects change points and outputs a list of detected indices.

---

### User Story 3 - Statistical Significance and Detectability Analysis (Priority: P3)

The researcher needs to aggregate F1-scores from multiple datasets, perform a non-parametric test to determine statistical significance, and correlate detection performance with shift characteristics (magnitude, duration, type) to identify which distributional changes are most amenable to Bayesian detection.

**Why this priority**: This validates the hypothesis and answers the core research question regarding shift characteristics. While critical for the research conclusion, it depends on the successful completion of Stories 1 and 2.

**Independent Test**: Can be fully tested by feeding a CSV of F1-scores and shift parameters from multiple datasets into the evaluation script and verifying the p-value output and the correlation matrix.

**Acceptance Scenarios**:

1. **Given** F1-scores for Bayesian and Baseline methods across ≥ 5 datasets, **When** the Wilcoxon signed-rank test is executed, **Then** it outputs a p-value indicating statistical significance (or lack thereof).
2. **Given** the GitHub Actions job limit, **When** the evaluation and plotting scripts complete, **Then** the total runtime for all analysis steps must not exceed 6 hours.
3. **Given** a set of shift parameters (magnitude, duration), **When** the detectability analysis runs, **Then** it outputs a correlation coefficient showing the relationship between shift magnitude and F1-score for the Bayesian model.

---

### Edge Cases

- What happens when the time series data contains missing values or extreme outliers that exceed the normalization bounds?
- How does the system handle non-stationary variance changes that violate the Gaussian Process prior assumptions?
- What happens if the 6-hour CI limit is exceeded during the MCMC/VI inference steps?
- How does the system handle datasets where the synthetic anomalies are too subtle to be detected by any method (floor effect)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load and normalize univariate time series data from public repositories (e.g., UCR, UCI) and store provenance metadata. (See US-1)
- **FR-002**: System MUST implement Gaussian Process regression with Sparse Variational Inference for anomaly scoring using a CPU-tractable library (e.g., PyMC or NumPyro). (See US-1)
- **FR-003**: System MUST implement Shewhart control charts, CUSUM procedures, and a Variational Auto-Encoder (VAE) as baseline comparators. (See US-2)
- **FR-004**: System MUST inject synthetic anomalies (mean shifts, variance spikes, gradual drifts) with configurable parameters (magnitude, variance ratio, duration) covering a range that includes near-threshold values to ensure fair comparison; specific ranges are [deferred] to the research phase. (See US-1)
- **FR-005**: System MUST calculate Precision, Recall, F1-score, and AUC-ROC for all model outputs against the injected ground truth. (See US-3)
- **FR-006**: System MUST execute a Wilcoxon signed-rank test on F1-scores across datasets to calculate and report the p-value for statistical significance between Bayesian and baseline methods. (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis on the anomaly detection threshold by sweeping the decision cutoff over a configurable range and reporting the variation in false-positive and false-negative rates. (See US-3)
- **FR-008**: System MUST frame all findings regarding shift detectability as associational, explicitly avoiding causal claims unless randomization is specified in the data generation process. (See US-3)
- **FR-009**: System MUST include a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) when evaluating performance across multiple hypothesis tests or datasets. (See US-3)
- **FR-010**: System MUST validate that the Gaussian Process kernel parameters are optimized via variational inference within the 1000-step limit to ensure convergence within the 6-hour CI job. (See US-1)
- **FR-011**: System MUST include a range of anomaly magnitudes (including near-threshold values) in the synthetic injection process to avoid floor effects where all methods achieve F1 ≈ 1.0. (See US-1)
- **FR-012**: System MUST define a fixed thresholding strategy (e.g., 95% specificity or F1-optimization) before correlating detection performance with shift characteristics to prevent threshold selection bias. (See US-3)

### Key Entities *(include if feature involves data)*

- **TimeSeriesWindow**: A segmented slice of univariate time data, normalized, associated with ground truth anomaly labels, and shift parameters.
- **AnomalyScore**: A numerical output representing the probability or deviation score of a specific time point being anomalous.
- **ShiftCharacteristic**: A structured record defining the type (mean/variance), magnitude, duration, and location of an injected anomaly.
- **EvaluationMetric**: Aggregated performance data (F1, AUC, p-value, correlation coefficients) comparing model performance against baselines and shift characteristics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system MUST execute a paired t-test (or Wilcoxon signed-rank test) and report the p-value comparing the Bayesian nonparametric model's F1-score against Shewhart charts on non-stationary datasets with abrupt variance changes. (See US-3)
- **SC-002**: The complete inference and evaluation pipeline completes within the standard GitHub Actions job limit on a 2-core CPU runner. (See US-3)
- **SC-003**: Peak memory usage during model inference remains within acceptable limits on standard CPU resources. (See US-1)
- **SC-004**: The sensitivity analysis measures the variation in F1-score when the decision threshold is swept across a configurable range. (See US-3)
- **SC-005**: The system calculates and reports the correlation coefficient between shift magnitude and F1-score to assess the relationship between shift size and detectability. (See US-3)

## Assumptions

- Public datasets from UCR or UCI repositories are accessible via direct download links and compatible with the preprocessing pipeline without requiring complex authentication.
- Synthetic anomalies injected into the data (mean shifts, variance spikes) accurately represent the ground truth for evaluation and do not introduce artifacts that invalidate the statistical properties of the time series.
- The target environment is a standard CPU-based CI runner (GitHub Actions free tier) without GPU acceleration, limiting the choice of libraries to CPU-optimized versions of PyMC or NumPyro.
- A sufficiently large inference limit is sufficient for the variational inference algorithm to converge to a stable solution for the selected Gaussian Process models on the chosen dataset sizes.
- The datasets selected for the study contain sufficient length to allow for meaningful windowing and anomaly injection without exhausting the available disk capacity.
- The "detectability" of a shift is defined strictly by the F1-score achieved against the injected ground truth, not by visual inspection or subjective assessment.