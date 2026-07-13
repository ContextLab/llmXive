# Feature Specification: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

**Feature Branch**: `001-assess-test-sensitivity`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How do Type I and Type II error rates of common statistical tests (t-test, ANOVA, chi-squared) vary as a function of sample size and underlying data distribution?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Controlled Synthetic Datasets for Null and Alternative Hypotheses (Priority: P1)

The system must generate synthetic datasets across a defined range of sample sizes (n=10 to n=1000) and three canonical distributions (normal, uniform, log-normal) with known ground truth parameters for both null (no effect) and alternative (effect size 0.5) conditions.

**Why this priority**: This is the foundational step. Without controlled data generation with known ground truth, no subsequent error rate calculation is possible. It directly enables the core research question.

**Independent Test**: Can be fully tested by verifying the generated data statistics (mean, variance, distribution shape) match the theoretical parameters for a specific sample size and distribution, ensuring the "ground truth" is accurate before running any statistical tests.

**Acceptance Scenarios**:

1. **Given** a request for a normal distribution with n=50 and effect size 0.0 (null), **When** the data generator runs, **Then** the resulting sample means of the two groups have a mean difference of 0.0 ± 1e-6 and the population parameters match the input exactly.
2. **Given** a request for a log-normal distribution with n=30 and effect size 0.5 (alternative), **When** the data generator runs, **Then** the generated data exhibits the specified skewness and the true mean difference between groups equals the input effect size (0.5 ± 1e-6).
3. **Given** a request for a uniform distribution with n=1000, **When** the data generator runs, **Then** the output data fits a uniform distribution profile and the sample size is exactly 1000.

---

### User Story 2 - Execute Monte Carlo Simulations for Error Rate Quantification (Priority: P2)

The system must perform an adaptive number of Monte Carlo replicates for each combination of test type (t-test, ANOVA, chi-squared), sample size, and distribution, starting with a minimum of 1000 replicates and extending until the 95% confidence interval width is ≤ 0.01. Results are classified as Type I or Type II errors based on a nominal alpha of 0.05 applied to the resulting p-value (regardless of whether the test is standard, continuity-corrected, or Fisher's Exact).

**Why this priority**: This executes the core methodology to quantify the sensitivity. It transforms raw data into the specific metrics (error rates) required to answer the research question.

**Independent Test**: Can be tested by running a small subset (e.g., 100 replicates) of a known scenario (e.g., t-test on normal data, n=50, null true) and verifying the observed Type I error rate is close to the theoretical 0.05, confirming the simulation loop logic is correct.

**Acceptance Scenarios**:

1. **Given** 1000 replicates of a t-test on normal data with true null hypothesis, **When** the simulation completes, **Then** the calculated Type I error rate falls within the 95% confidence interval of the binomial distribution with n=1000, p=0.05 (specifically [0.036, 0.064]).
2. **Given** 1000 replicates of an ANOVA on skewed data with a true alternative hypothesis (effect size 0.5), **When** the simulation completes, **Then** the system correctly counts the number of failures to reject the null (Type II errors) and calculates the power (1 - Type II rate).
3. **Given** a chi-squared test on contingency tables with n=20, **When** the simulation runs, **Then** the system detects expected cell counts < 5, switches to Fisher's Exact Test, and produces a valid error rate count.

---

### User Story 3 - Aggregate Results and Generate Visualizations for Interpretation (Priority: P3)

The system must aggregate the error rates by sample size, distribution, and test type, compute 95% confidence intervals via bootstrap, and export publication-ready visualizations (PNG/SVG) and CSV data. Additionally, it must fit regression models to analyze the magnitude of deviation from nominal alpha.

**Why this priority**: This delivers the final value to the user (researchers/practitioners) by making the empirical mapping between sample size, distribution, and test reliability interpretable and usable.

**Independent Test**: Can be tested by verifying that the generated CSV contains all expected columns (sample size, distribution, test type, error rate, CI_lower, CI_upper) and that the generated plots correctly map sample size to error rate with visible confidence intervals.

**Acceptance Scenarios**:

1. **Given** the aggregated simulation results, **When** the export function runs, **Then** a CSV file is generated containing error rates for all 20 sample sizes × 3 distributions × 3 tests, with calculated 95% CIs.
2. **Given** the error rate data for t-tests across normal and skewed distributions, **When** the visualization module runs, **Then** a plot is generated showing error rate curves with sample size on the x-axis, clearly distinguishing the two distributions.
3. **Given** the full dataset, **When** the regression analysis runs, **Then** the system outputs regression coefficients (beta) and p-values for predictors (sample size, distribution type, test type) where at least one predictor has p < 0.05 and the model achieves a McFadden pseudo-R² > 0.1.

### Edge Cases

- **Small Sample Instability**: What happens when n < 10? The system must handle the lower bound (n=10) gracefully, acknowledging potential instability in error rate estimates for very small samples.
- **Distribution Extremes**: How does the system handle the log-normal distribution with high skew? The generator must ensure the skew is defined but finite to prevent numerical overflow during generation.
- **Chi-Squared Small Counts**: How does the system handle chi-squared tests with expected cell counts < 5? The simulation MUST use Fisher's Exact Test for these configurations to ensure scientific validity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic datasets for three distributions (normal, uniform, log-normal) across 20 specific sample sizes (n=10 to n=1000) with known ground truth parameters for null and alternative hypotheses. (See US-1)
- **FR-002**: System MUST execute Monte Carlo replicates for each combination of test type (t-test, ANOVA, chi-squared), sample size, and distribution. The system MUST start with 1000 replicates and automatically extend the run with additional replicates until the 95% confidence interval width for the error rate is ≤ 0.01. For chi-squared tests where expected cell counts < 5, the system MUST use Fisher's Exact Test. (See US-2)
- **FR-003**: System MUST classify simulation outcomes as Type I errors (rejecting true null) or Type II errors (failing to reject false null) using a fixed nominal alpha threshold of 0.05 applied to the resulting p-value from the selected test (standard, Fisher's Exact, or ANOVA). (See US-2)
- **FR-004**: System MUST compute 95% confidence intervals for all error rate estimates using bootstrap resampling methods. If the computed 95% CI width exceeds 0.01, the system MUST trigger additional replicates until the width is ≤ 0.01. (See US-3)
- **FR-005**: System MUST export results to a CSV file containing sample size, distribution type, test type, error rate, and confidence interval bounds, and generate publication-ready PNG/SVG visualizations. (See US-3)
- **FR-006**: System MUST fit regression models to predict the magnitude of deviation from nominal alpha (|p - 0.05|) and the log-transformed p-value distribution based on log-transformed sample size, distribution type, and test type, reporting regression coefficients (beta) and their significance (p-values). (See US-3)

### Key Entities

- **SimulationRun**: Represents a single iteration of data generation and testing for a specific (n, distribution, test) configuration.
- **ErrorMetric**: Represents the aggregated outcome (Type I rate, Type II rate, Power) for a specific configuration, including confidence intervals.
- **Configuration**: Defines the parameters of a simulation batch (sample size list, distribution types, effect sizes).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The observed Type I error rate for t-tests on normal data (null true) is measured against the theoretical nominal alpha level of 0.05 to validate the simulation engine. (See US-2)
- **SC-002**: The stability of Type I error rates for t-tests and ANOVA under normal distributions is measured across the full range of sample sizes (n=10 to n=1000) to confirm robustness. (See US-3)
- **SC-003**: The inflation of Type I error rates for tests under skewed distributions at small sample sizes (n<30) is measured against the nominal alpha of 0.05 to quantify the degree of deviation. (See US-3)
- **SC-004**: The reduction rate of Type II error rates (increase in power) is measured as a function of increasing sample size for each test type, where success is defined as the observed power curve matching the theoretical power curve within a mean absolute error of 0.02. (See US-3)
- **SC-005**: The impact of distribution type on error rates is measured via regression analysis, where success is defined as the model achieving a McFadden pseudo-R² > 0.1. (See US-3)

## Assumptions

- **Assumption about data generation**: The project assumes that Python's `numpy` and `scipy` libraries are sufficient to generate the required synthetic distributions (normal, uniform, log-normal) with the specified parameters and that these libraries run efficiently on CPU-only environments.
- **Assumption about compute constraints**: The project assumes that the total computational load (20 sample sizes × 3 distributions × 3 tests × adaptive replicates) fits within the 6-hour time limit and 7 GB RAM constraint of the GitHub Actions free-tier runner when executed sequentially or with limited parallelism.
- **Assumption about statistical validity**: The project assumes that the nominal alpha level of 0.05 is the standard threshold for classification and that the Monte Carlo approach provides a valid approximation of the true error rates for the defined distributions.
- **Assumption about collinearity**: Since the predictors (sample size, distribution type) are distinct and not definitionally related, no collinearity diagnostics are required for the regression model.
- **Assumption about threshold justification**: The alpha threshold of 0.05 is a community-standard default for hypothesis testing; therefore, no sensitivity analysis sweeping the alpha value is required for this specific study, though the results are explicitly tied to this value.