# Feature Specification: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Feature Branch**: `001-bayesian-nonparametrics-for-anomaly-detection`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "Bayesian Nonparametrics for Anomaly Detection in Time Series"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core DPGMM Training and Dynamic Signature Extraction (Priority: P1)

The system MUST implement a stick-breaking Dirichlet Process Gaussian Mixture Model (DP-GMM) using PyMC with ADVI variational inference to process univariate time series data in sliding windows, explicitly tracking the temporal evolution of the concentration parameter ($\alpha$) and component weights ($\pi$) to extract dynamic signatures.

**Why this priority**: This is the core research contribution; without the ability to train the nonparametric model and extract the specific temporal derivatives of $\alpha$ and $\pi$, the hypothesis regarding "early-warning signatures" cannot be tested.

**Independent Test**: Can be fully tested by loading a synthetic dataset with injected anomalies, running the sliding window inference, and verifying that the output includes a time-series of posterior mean $\alpha$, its first derivative, and component weight variance for every window step.

**Acceptance Scenarios**:

1. **Given** a univariate time series with ≥1,000 observations and injected anomalies, **When** the sliding window (length=30, stride=1) inference runs, **Then** the system outputs a trajectory of posterior $\alpha$ means and their first derivatives for every window step.
2. **Given** a trained DPGMM on a normal segment, **When** processing an abrupt regime shift, **Then** the system records a distinct high-frequency oscillation or spike (frequency > 0.1 Hz and amplitude > 3 standard deviations above baseline) in the rate of change of $\alpha$ compared to the baseline drift.
3. **Given** the incremental update logic, **When** processing the next window, **Then** the posterior is updated without full retraining, ensuring the core DP-GMM training phase runtime remains <6 hours on a 2-core CPU.
4. **Given** a dataset with gradual, benign non-stationarity (negative control), **When** processing the data, **Then** the system does not produce a spike in the rate of change of $\alpha$ (frequency ≤ 0.1 Hz and amplitude ≤ 3 standard deviations above baseline), and a two-sample KS test (FR-014) confirms the distribution of signatures differs significantly from the anomaly group (p < 0.05).

---

### User Story 2 - Baseline Comparison and Time-to-Detection Analysis (Priority: P2)

The system MUST compute standard anomaly scores (reconstruction error) from fixed-component GMMs (k=3, 5, 10) and ARIMA models on the same sliding windows, and calculate the "time-to-detection" (steps from injection to threshold crossing) for both the DP-GMM dynamic signatures and the baselines.

**Why this priority**: Required to validate the "early-warning" claim; the research question explicitly asks if DP-GMM dynamics detect anomalies *before* the posterior converges, which requires a direct comparison against static baselines.

**Independent Test**: Can be fully tested by running the baseline models and DP-GMM on the same data, computing time-to-detection for each, and verifying that the DP-GMM signature detects the anomaly significantly earlier (statistically significant difference) than the baselines.

**Acceptance Scenarios**:

1. **Given** a dataset with known anomaly onset timestamps (independent ground-truth), **When** running the baseline comparison, **Then** the system computes reconstruction errors (MSE) for fixed GMMs and ARIMA for every window.
2. **Given** the dynamic signature trajectories and baseline scores, **When** calculating time-to-detection, **Then** the system records the number of steps from injection to the first threshold crossing for each method.
3. **Given** the collected time-to-detection values, **When** performing the paired t-test across datasets, **Then** the system outputs a p-value indicating if the DP-GMM detection time is significantly shorter than the baselines.
4. **Given** the distribution of "rate of change" metrics for anomaly and normal windows, **When** performing the KS test, **Then** the system outputs the KS statistic and p-value to confirm distributional differences.

---

### User Story 3 - Threshold Justification and Sensitivity Analysis (Priority: P3)

The system MUST implement a sensitivity analysis for the anomaly detection threshold, sweeping the cutoff over a concrete set of absolute values (e.g., a range of low to moderate thresholds) and reporting how the false-positive and false-negative rates vary across these thresholds.

**Why this priority**: The methodology panel requires that any decision cutoff introduced in the design carries a justification and a sensitivity analysis to ensure the results are not artifacts of a specific arbitrary threshold.

**Independent Test**: Can be fully tested by running the detection logic with three distinct threshold values and verifying that the output includes a table or plot showing the variation in error rates (FP/FN) across these values.

**Acceptance Scenarios**:

1. **Given** a detection threshold (default 95th percentile of score distribution), **When** running the sensitivity analysis, **Then** the system re-evaluates detection performance at absolute cutoff values of 0.01, 0.05, and 0.1.
2. **Given** the results of the sensitivity sweep, **When** generating the report, **Then** the system explicitly states the baseline community-standard justification for the default threshold (citing Cohen, 1988) and lists the observed variation in false-positive rates across the sweep.
3. **Given** the sensitivity results, **When** the system detects a threshold where error rates spike, **Then** it flags this instability in the final analysis report.

---

### User Story 4 - Resource Constraint Validation and CPU Feasibility (Priority: P3)

The system MUST validate that the entire analysis pipeline (data loading, sliding window inference, baseline comparison, and statistical testing) completes within the GitHub Actions free-tier constraints: ≤2 CPU cores, ~7 GB RAM, and ≤6 hours total runtime.

**Why this priority**: The project cannot reach `research_complete` if the analysis fails to run on the target hardware; this ensures the methodology is computationally feasible without GPU acceleration.

**Independent Test**: Can be fully tested by executing the full pipeline on a standard GitHub Actions runner and verifying that peak memory usage stays <7 GB and total runtime is <6 hours.

**Acceptance Scenarios**:

1. **Given** the largest supported dataset (e.g., Electricity Load Diagrams), **When** running the full pipeline, **Then** peak RAM usage remains <7 GB throughout execution (measured via `psutil.Process().memory_info().rss`).
2. **Given** the full pipeline execution, **When** measuring total runtime, **Then** the job completes in <6 hours without timing out.
3. **Given** the inference engine, **When** running on the CPU-only runner, **Then** the system never attempts to load CUDA libraries or request GPU memory.

---

### Edge Cases

- What happens when a dataset has <1,000 observations? → System MUST reject with a validation error stating the dataset size is insufficient for the sliding window analysis (minItems: 1000).
- How does the system handle non-convergent ADVI runs? → If the ELBO fails to converge (delta > 0.01 for 10 iterations) within 500 iterations, the model for that specific window is excluded from the trajectory, and a warning is logged (logs string "WARNING: ADVI did not converge" to stderr); the analysis proceeds with available data.
- What happens when the anomaly injection rate is too low for statistical power? → The system performs a power analysis check; if the expected number of anomalies is <10 (based on a 1-5% injection rate in datasets ≥1,000 observations), it flags a warning and proceeds with descriptive statistics. For inferential testing (paired t-tests, KS tests), the design mandates a minimum of 10 observed anomalies to achieve ≥80% statistical power at α=0.05 for detecting a moderate effect size (Cohen's d=0.5), consistent with standard power analysis conventions for anomaly detection studies (see Cohen, 1988). If the dataset yields <10 anomalies, the system automatically switches to a non-parametric bootstrap resampling method to estimate detection significance, ensuring the pipeline remains robust without requiring manual intervention.
- How does the system handle datasets with missing timestamps? → The system assumes the data is sorted by time and generates synthetic integer timestamps (0, 1, 2...) for indexing if real timestamps are missing, as the analysis relies on relative order.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load univariate time series datasets with ≥1,000 observations, normalizing them to zero mean and unit variance before processing (See US-1)
- **FR-002**: System MUST implement a stick-breaking DP-GMM using PyMC 4 with ADVI variational inference, tracking the posterior mean of the concentration parameter ($\alpha$) and component weights ($\pi$) at each sliding window step (See US-1). Note: The derivative of $\alpha$ is a proxy signal subject to validation against ground-truth.
- **FR-003**: System MUST compute the first derivative (rate of change) of the posterior mean $\alpha$ and the variance of component weights for every time step $t$ (See US-1)
- **FR-004**: System MUST fit fixed-component GMMs (k=3, 5, 10) and an ARIMA model on the same sliding windows to serve as baselines for reconstruction error comparison (See US-2)
- **FR-005**: System MUST calculate "time-to-detection" (steps from injection to threshold crossing) for both DP-GMM dynamic signatures and baseline reconstruction errors (See US-2)
- **FR-006**: System MUST perform a paired t-test on time-to-detection values across multiple datasets to assess statistical significance of earlier detection by DP-GMM (See US-2)
- **FR-007**: System MUST implement a sensitivity analysis for the anomaly detection threshold, sweeping the cutoff over the set {0.01, 0.05, 0.1} and reporting the variation in false-positive and false-negative rates (See US-3)
- **FR-008**: System MUST validate memory usage (<7 GB) and total runtime (<6 hours) on a CPU-only environment, excluding any GPU-dependent operations (See US-4)
- **FR-009**: System MUST exclude models from evaluation if the ADVI ELBO fails to converge (delta > 0.01 for 10 consecutive iterations) within 500 iterations (See US-1, US-4)
- **FR-010**: System MUST perform a Kolmogorov-Smirnov test to compare the distribution of "rate of change" metrics between anomaly and normal windows (See US-2)
- **FR-011**: System MUST perform a power analysis check; if the expected number of anomalies is <10, the system MUST flag a warning and proceed with descriptive statistics rather than inferential testing (See US-1)
- **FR-012**: System MUST switch to a non-parametric bootstrap resampling method to estimate detection significance if the dataset yields <10 anomalies (See US-1)
- **FR-013**: System MUST define "time-to-detection" against an independent ground-truth injection timestamp that is distinct from the model's own trajectory (See US-2)
- **FR-014**: System MUST perform a two-sample KS test to compare the distribution of "rate of change" metrics between transient anomalies and gradual drift (negative control) (See US-1)
- **FR-015**: System MUST perform a statistical test (KS test) for distribution comparison of baseline metrics rather than relying solely on a t-test on detection times (See US-2)
- **FR-016**: System MUST implement a sensitivity analysis on window size and derivative calculation method (smoothing, lag) to validate the robustness of the "rate of change" signal (See US-3)
- **FR-017**: System MUST validate the dynamic signature against a dataset with known real-world regime shifts (e.g., documented grid failure) to ensure generalizability (See US-1)

### Key Entities

- **TimeSeriesWindow**: A sliding window of univariate data (length=30, stride=1) used for local distributional estimation.
- **PosteriorTrajectory**: The time-series record of posterior means for $\alpha$ and $\pi$, and their derivatives, extracted from the DP-GMM.
- **DetectionEvent**: A record containing the timestamp of anomaly injection, the detection timestamp by a specific method, and the calculated time-to-detection.
- **SensitivityReport**: A structured output listing the threshold values tested and the corresponding false-positive/false-negative rates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The distinctness of dynamic signatures (oscillation frequency/rate of change) is measured against the ground-truth injection timestamps of transient anomalies versus gradual drift, quantified as Cohen's d ≥ 0.5 (See US-1)
- **SC-002**: The time-to-detection advantage of DP-GMM over baselines is measured against the paired t-test p-value across the three datasets (See US-2)
- **SC-003**: The stability of the detection threshold is measured against the variation in false-positive rates across the sensitivity sweep {0.01, 0.05, 0.1} (See US-3)
- **SC-004**: The computational feasibility is measured against the peak RAM usage (<7 GB) and total runtime (<6 hours) on the GitHub Actions runner (See US-4)
- **SC-005**: The statistical power for detecting anomalies is measured against the expected number of anomalies in the dataset (target ≥10) given the 1-5% injection rate; if <10, the system proceeds with bootstrap resampling as per FR-012 (See US-1)
- **SC-006**: The fallback to bootstrap resampling is measured against the successful execution of the bootstrap procedure when anomaly count <10 (See US-1)
- **SC-007**: The distributional difference between anomaly and normal windows is measured against the KS statistic and p-value from FR-014 (See US-1)

## Assumptions

- The UCI/OpenML datasets (Electricity Load Diagrams, Air Quality, Sensors) contain sufficient observations (≥1,000) and are univariate or can be reduced to a single representative univariate series without losing the target regime shift characteristics.
- ADVI variational inference in PyMC 4 is capable of converging adequately for the DP-GMM on the specified sliding window size (30) within 500 iterations; if convergence fails, the model is excluded as per FR-009 rather than switching to MCMC (which would violate CPU constraints).
- The synthetic anomaly injection process (point anomalies, abrupt shifts, gradual drift) accurately simulates the real-world phenomena described in the research question, and the ground-truth labels generated by the injection script are independent of the model's inference.
- The GitHub Actions free-tier runner (standard CPU allocation, ~7 GB RAM) is sufficient to run the ADVI inference and baseline comparisons for the specified dataset sizes; no GPU acceleration or 8-bit quantization is required or used.
- The "rate of change" of the concentration parameter $\alpha$ is a valid and observable proxy for the "early-warning" signal, and its behavior (oscillation vs. smooth drift) is distinguishable between the two regime types. Note: In small windows (n=30), the posterior for $\alpha$ may be dominated by the prior or noise, making the derivative a high-variance signal subject to validation.
- The power analysis assumption holds: with ≥1,000 observations and a 1-5% anomaly rate, the expected number of anomalies (10-50) is sufficient for the statistical tests (KS test, t-test) to have reasonable power, though a formal power calculation is deferred to the implementation phase.
- The sliding window length and stride are selected to be optimal for capturing short-term distributional properties without introducing excessive computational overhead or latency.
- Synthetic anomaly injection may not fully capture complex, multivariate dependencies of real regime shifts; validation against real-world datasets (FR-017) is required to ensure generalizability.