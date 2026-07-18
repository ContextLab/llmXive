# Feature Specification: Assessing the Impact of Data Ordering on Bootstrapping Results

**Feature Branch**: `001-assess-data-ordering-bootstrapping`
**Created**: 2024-05-22
**Status**: Draft
**Input**: User description: "Assessing the Impact of Data Ordering on Bootstrapping Results"

## User Scenarios & Testing

### User Story 1 - Simulate Autocorrelated Data and Compute Coverage (Priority: P1)

The system MUST generate synthetic time series data with known autocorrelation structures, apply standard non-parametric bootstrapping to the ordered data, and calculate the empirical coverage probability of the 95% confidence interval against the theoretical mean of the process.

**Why this priority**: This is the core mechanism of the research. Without the ability to generate data with controlled autocorrelation and measure the resulting coverage degradation, the project cannot answer the primary research question. It represents the minimum viable research unit.

**Independent Test**: The system can be tested by running a simulation with a fixed autoregressive coefficient ($\phi = 0.8$) and verifying that the calculated coverage probability is significantly lower than 0.95 (e.g., < 0.90) [deferred] trials, confirming the failure mode.

**Acceptance Scenarios**:

1. **Given** a target autoregressive coefficient $\phi \in [0.0, 0.9]$, **When** the system generates [deferred] independent AR(1) time series samples of size $N \in \{50, 100, 200\}$, **Then** the system calculates the theoretical mean for each series (0) and the standard bootstrap 95% CI, reporting the percentage of CIs containing the theoretical mean.
2. **Given** a sequence of $\phi$ values from 0.0 to 0.9 in increments of 0.1, **When** the simulation runs, **Then** the system outputs a mapping of $\phi$ to observed coverage probability, demonstrating a monotonic decrease in coverage as $\phi$ increases.

### User Story 2 - Compare Ordered vs. Shuffled Baselines (Priority: P2)

The system MUST apply the same bootstrapping procedure to the data after random permutation (shuffling) to break temporal dependence and compare the resulting coverage probabilities against the ordered data baseline. The "true mean" used for coverage calculation is the theoretical process mean (0), ensuring the comparison is valid even if the sample mean shifts. The system MUST measure the *magnitude* of the coverage drop (difference between empirical coverage and nominal 0.95) rather than relying solely on a significance test.

**Why this priority**: This establishes the counterfactual. It isolates "order" as the variable causing the bias by showing that the same data, when shuffled, restores nominal coverage. This confirms the mechanism is temporal dependence, not data distribution shape.

**Independent Test**: The system can be tested by running the simulation on a single dataset with $\phi=0.5$, comparing the coverage rate of the ordered version (expected < 0.95) against the shuffled version (expected $\approx$ 0.95), and verifying the system outputs the difference in coverage probability and performs a two-proportion z-test on the aggregate counts.

**Acceptance Scenarios**:

1. **Given** a generated AR(1) time series with $\phi > 0.5$, **When** the system runs bootstrapping on both the original ordered sequence and a randomly shuffled permutation of the same data, **Then** The coverage probability of the shuffled data is within a small margin of the nominal 0.95 level, while the ordered data is below 0.90..
2. **Given** a set of 1,000 simulation trials, **When** the system performs a two-proportion z-test comparing the coverage indicators of ordered vs. shuffled conditions on the aggregate counts, **Then** the system outputs the calculated p-value and the difference in coverage proportions.

### User Story 3 - Analyze Real-World Data Segments (Priority: P3)

The system MUST load the UCI Individual Household Electric Power Consumption dataset, segment it into hourly windows, estimate the autocorrelation for each segment, and run the ordered-vs-shuffled bootstrap comparison to validate findings on empirical data. For real-world data, the system MUST NOT calculate coverage against a theoretical mean of 0 (which does not exist); instead, it MUST measure CI Width Stability and Bias Relative to a Block-Bootstrap reference.

**Why this priority**: This extends the synthetic findings to a real-world context, addressing the "practitioner" aspect of the motivation. It validates that the synthetic behavior holds in messy, real data, though it is secondary to the controlled synthetic proof.

**Independent Test**: The system can be tested by loading the UCI dataset, identifying at least 50 hourly windows, and confirming that the system outputs the relationship between estimated $\phi$ and the magnitude of the coverage drop (for synthetic) or CI Width Stability (for real data).

**Acceptance Scenarios**:

1. **Given** the UCI Individual Household Electric Power Consumption dataset, **When** the system segments the data into non-overlapping hourly windows and estimates the AR(1) coefficient for each, **Then** the system processes ALL valid segments (no filtering for $\phi > 0.3$) and reports results stratified by $\phi$ bins.
2. **Given** a subset of real-world hourly windows, **When** the system compares ordered vs. shuffled bootstrap metrics, **Then** the system outputs the mean difference in CI width between ordered and shuffled conditions and the bias relative to the block-bootstrap estimate.

### Edge Cases

- What happens when the autocorrelation coefficient $\phi$ is exactly 0.0 (white noise)? The system should show no significant difference between ordered and shuffled coverage.
- How does the system handle datasets with missing values in the UCI source? The system MUST drop or impute missing values consistently before segmentation to avoid bias in autocorrelation estimation.
- What if the time series length is too short (e.g., $N < 30$) to estimate $\phi$ reliably? The system MUST skip such segments and output a JSON object with "status": "skipped" and "reason": "insufficient_data" rather than producing noisy estimates.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic AR(1) time series data with a user-specified autoregressive coefficient $\phi \in [0.0, 0.9]$ and sample sizes $N \in \{50, 100, 200\}$ for sensitivity analysis (See US-1).
- **FR-002**: System MUST perform standard non-parametric bootstrapping (a sufficient number of resamples) to construct 95% confidence intervals for the mean of the input data (See US-1).
- **FR-003**: System MUST calculate the empirical coverage probability as the percentage of generated confidence intervals that contain the theoretical mean of the process (0) for synthetic data ONLY. For real-world data, this metric is not applicable; see FR-010 for alternative metrics (See US-1).
- **FR-004**: System MUST implement a shuffling mechanism that randomly permutes the input data array to break temporal dependence while preserving the marginal distribution (See US-2).
- **FR-005**: System MUST perform a two-proportion z-test on the aggregate counts of covered/not-covered trials (across [deferred] trials) to compare ordered vs. shuffled conditions, and MUST report the magnitude of the coverage drop (absolute difference between empirical coverage and nominal 0.95) (See US-2).
- **FR-006**: System MUST load and parse the UCI Individual Household Electric Power Consumption dataset from the verified URL ` and verify the file integrity using MD5 checksum. If verification fails, the system MUST raise an explicit error and halt execution (See US-3).
- **FR-007**: System MUST segment the real-world dataset into non-overlapping hourly windows, process ALL valid segments (no pre-filtering by $\phi$), estimate the AR(1) coefficient for valid segments using `statsmodels`, and skip segments with $N < 30$ by logging a JSON object with "status": "skipped" and "reason": "insufficient_data" to the output log (See US-3).
- **FR-008**: System MUST output a summary report containing the coverage probabilities for ordered vs. shuffled data across all $\phi$ levels and the p-values of the significance tests (See US-1, US-2).
- **FR-009**: System MUST stratify real-world analysis results by $\phi$ bins (e.g., 0.0-0.1, 0.1-0.2, etc.) to demonstrate the continuous degradation of coverage as a function of autocorrelation (See US-3).
- **FR-010**: System MUST calculate CI Width Stability (ratio of ordered/shuffled CI widths) and Bias Relative to Block-Bootstrap for real-world data segments, as standard coverage against a theoretical mean is invalid for real data (See US-3).
- **FR-011**: System MUST include a sensitivity analysis report comparing coverage probabilities across sample sizes $N=50, 100, 200$ to confirm the effect is due to autocorrelation and not small-sample artifacts (See US-1).

### Key Entities

- **TimeSeries**: Represents a sequence of observations with an associated autoregressive coefficient $\phi$ and theoretical mean (0).
- **BootstrapResult**: Represents the outcome of a single bootstrap run, including the confidence interval bounds and a boolean indicating if the theoretical mean was covered.
- **SimulationBatch**: A collection of 1,000 `BootstrapResult` instances for a specific $\phi$ level and sample size, used to calculate coverage probability.
- **DataSegment**: A subset of the UCI dataset corresponding to one hour, with an estimated autocorrelation value and a status flag (valid/skipped).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in coverage probability between ordered and shuffled data is measured against the nominal 0.95 level to quantify the bias introduced by temporal autocorrelation (See US-1).
- **SC-002**: The statistical significance of the coverage difference is measured against the critical value for a two-proportion z-test at $\alpha = 0.05$ (See US-2).
- **SC-003**: The empirical coverage probability for synthetic data is measured against the nominal 0.95 level; for real-world data, the CI Width Stability and Bias Relative to Block-Bootstrap are measured against the shuffled baseline to validate the generalizability of the findings (See US-3).
- **SC-004**: The computational runtime of the full simulation (multiple trials $\times$ multiple $\phi$ levels $\times$ 3 sample sizes) is measured against the 6-hour limit of the free-tier GitHub Actions runner to ensure feasibility (See FR-001).
- **SC-005**: The sensitivity of the coverage probability to the sample size $N$ is measured by comparing results for $N=50, 100, 200$ to ensure the effect is not an artifact of small sample size (See FR-011).

## Assumptions

- The `statsmodels` library is available in the GitHub Actions free-tier environment and can be installed without GPU dependencies.
- The UCI Individual Household Electric Power Consumption dataset is accessible via the verified URL ` and the file integrity can be verified using MD5 checksum.
- The synthetic AR() generation assumes a Gaussian error term with a mean of zero and variance of one., which is sufficient for testing the exchangeability violation.
- The sample size $N \in \{, 100, 200\}$ is sufficient to estimate the mean and standard deviation and allow a substantial number of bootstrap resamples to run within the 6-hour compute limit.
- The "true mean" for synthetic data is the theoretical process mean (0), serving as the ground truth for coverage calculation.
- For real-world data, the "ground truth" is approximated by the Block-Bootstrap estimate, as the true population mean is unknown.
- A two-proportion z-test on aggregate counts is an appropriate approximation for the paired simulation design, avoiding the need for computationally expensive exact tests.
- No GPU acceleration is required or available; all computations rely on standard CPU floating-point operations.