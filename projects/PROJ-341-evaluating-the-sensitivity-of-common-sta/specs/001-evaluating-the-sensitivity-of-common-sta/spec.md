# Feature Specification: Evaluating the Sensitivity of Common Statistical Tests to Dataset Size

**Feature Branch**: `001-evaluating-sensitivity-statistical-tests`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How do Type I and Type II error rates of common parametric statistical tests (t-test, ANOVA, chi-squared) change as sample size decreases, and at what threshold do these tests become unreliable for practical inference?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Simulation Engine for Type I/II Error Estimation (Priority: P1)

A researcher needs to run a simulation that generates synthetic data with known ground truth (null and alternative hypotheses) across a range of sample sizes (n=5 to n=500) to empirically calculate the Type I and Type II error rates for standard parametric tests (t-test, ANOVA, chi-squared) with a minimum of 10,000 iterations per condition to ensure statistical stability.

**Why this priority**: This is the foundational capability; without accurate error rate estimation, no threshold analysis or reliability guidance can be generated. It directly addresses the core research question.

**Independent Test**: The system can be tested by running the simulation for a single condition (e.g., t-test, n=20, effect size 0.5) and verifying that the output file contains the raw p-values and the calculated empirical error rates (proportion of rejections) which match the expected binomial distribution variance for the configured iteration count (e.g., [deferred]).

**Acceptance Scenarios**:
1. **Given** a defined sample size (n), effect size, and test type, **When** the simulation runs 10,000 iterations, **Then** the system outputs a CSV containing the raw p-values and a summary row with the calculated empirical Type I (if null true) or Type II (if alternative true) error rate.
2. **Given** the null hypothesis is true (effect size = 0), **When** the t-test is applied across [deferred] iterations at n=30, **Then** the empirical Type I error rate is recorded and stored for threshold analysis.
3. **Given** the alternative hypothesis is true (effect size > 0), **When** the t-test is applied across [deferred] iterations at n=10, **Then** the empirical Type II error rate (1 - power) is recorded and stored.

---

### User Story 2 - Threshold Identification and Reliability Visualization (Priority: P2)

A researcher needs to visualize the relationship between sample size and error rates to identify the specific sample size threshold where error rates deviate significantly from the nominal alpha level (0.05) or where power drops below an acceptable level (e.g., 0.80).

**Why this priority**: This translates raw simulation data into actionable insights, fulfilling the "at what threshold" part of the research question. It provides the visual evidence required for study design guidance.

**Independent Test**: The system can be tested by feeding it the output CSV from User Story 1 and generating a plot where the X-axis is sample size and the Y-axis is error rate, with a horizontal line at 0.05 (for Type I) or 0.20 (for Type II), and a highlighted vertical line indicating the calculated threshold where the confidence interval crosses the nominal limit.

**Acceptance Scenarios**:
1. **Given** the simulation results for t-test Type I errors across n=5 to n=500, **When** the visualization is generated, **Then** the plot displays the empirical error rate curve with 95% binomial confidence intervals (Wilson score) and clearly marks the sample size where the lower bound of the CI exceeds 0.05.
2. **Given** the simulation results for Type II errors across varying effect sizes, **When** the power curve is plotted, **Then** the system identifies and annotates the minimum sample size required to achieve ≥ 0.80 power (Type II error ≤ 0.20) for each effect size.
3. **Given** multiple test types (t-test, ANOVA, chi-squared), **When** results are compared, **Then** a comparative plot shows the divergence of error rates for each test type at low sample sizes (n < 30).

---

### User Story 3 - Validation Against Real-World Small-Sample Datasets (Priority: P3)

A researcher needs to validate the simulation findings by applying the identified thresholds to 2-3 public small-sample datasets (e.g., from UCI or OpenML) to confirm that the simulated p-value distributions and bootstrapped power estimates align with observed behavior in real data.

**Why this priority**: This adds external validity to the simulation results, ensuring the findings are not artifacts of the synthetic data generation process. It is a "nice-to-have" for robustness but not strictly required for the core simulation logic.

**Independent Test**: The system can be tested by loading a public dataset with a known small sample size, applying the statistical tests, and verifying that the observed p-value distribution or bootstrapped power estimates fall within the confidence intervals predicted by the simulation for that sample size.

**Acceptance Scenarios**:
1. **Given** a public small-sample dataset (n < 50) with a known effect direction (based on literature), **When** the t-test is applied, **Then** the resulting p-value is consistent with the expected probability of rejection derived from the simulation curve for that n (i.e., p < 0.05 if the simulation predicts high power for that effect size).
2. **Given** a dataset where the null hypothesis is theoretically plausible, **When** the chi-squared test is run on the small sample, **Then** the observed p-value is compared against the simulated rejection probability for that n to assess consistency, rather than calculating a false positive frequency.
3. **Given** the validation results, **When** a report is generated, **Then** it explicitly states whether the simulated p-value distributions and bootstrapped power estimates held true for the real-world data or if significant deviations were observed.

---

### Edge Cases

- What happens when the sample size is extremely small (n < 5) where normality assumptions for t-tests are severely violated? The system should flag these conditions and report the failure of the test assumptions or the divergence from theoretical distributions.
- How does the system handle the chi-squared test when expected cell counts are < 5 in the simulated contingency tables? The system must detect this condition and either apply Yates' continuity correction or Fisher's Exact Test as a fallback, recording which method was used.
- What occurs if the random number generator seed is not fixed, leading to non-reproducible error rates? The system must enforce a deterministic seed for the simulation run to ensure reproducibility of the configured iteration count.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic datasets for t-test, ANOVA, and chi-squared scenarios with known ground truth (null and alternative) across sample sizes n=5 to n=500 in increments of 5, performing at least 10,000 iterations per condition (See US-1).
- **FR-002**: System MUST calculate empirical Type I error rates (proportion of p < 0.05 when null is true) and Type II error rates (proportion of p > 0.05 when alternative is true) for every sample size and effect size combination (See US-1).
- **FR-003**: System MUST compute 95% binomial confidence intervals (using Wilson score intervals) for all calculated error rates to quantify estimation uncertainty (See US-2).
- **FR-004**: System MUST identify and report the specific sample size threshold where the lower bound of the Type I error CI exceeds the nominal alpha (0.05) or where power drops below 0.80, defined as the smallest n where the power CI remains below 0.80 for 3 consecutive sample size increments (See US-2).
- **FR-005**: System MUST generate comparative visualizations (line plots with confidence bands) mapping sample size to error rates for all three test types (See US-2).
- **FR-006**: System MUST validate simulation results against 3 specific public small-sample datasets: UCI Breast Cancer (Wisconsin Diagnostic), UCI Wine, and OpenML Adult (subset), by comparing observed p-value distributions and bootstrapped power estimates with simulated predictions (See US-3).
- **FR-007**: System MUST detect and handle chi-squared test violations (expected cell count < 5) by applying Yates' correction or Fisher's Exact Test and logging the method used (See Edge Cases).

### Key Entities

- **SimulationCondition**: Represents a unique configuration of test type, sample size, effect size, and hypothesis state (null/alternative).
- **ErrorRateResult**: Represents the output of a simulation run, containing the sample size, effect size, empirical error rate, confidence interval bounds, and iteration count.
- **ThresholdMetric**: Represents the identified sample size where error rates deviate from nominal levels, including the specific test type and effect size context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The deviation of empirical Type I error rates from the nominal 0.05 level is measured against the 95% Wilson score confidence interval to determine if the test is reliable at a given sample size (See FR-003, FR-004).
- **SC-002**: The minimum sample size required to achieve power ≥ 0.80 (Type II error ≤ 0.20) is measured against the simulated power curves for small, medium, and large effect sizes (See FR-004, US-2).
- **SC-003**: The consistency between simulated p-value distributions and those derived from public small-sample datasets is measured against the Kolmogorov-Smirnov (KS) distance statistic, requiring a KS statistic ≤ 0.10 to indicate alignment (See FR-006, US-3).
- **SC-004**: The robustness of the threshold identification is measured by performing a sensitivity analysis where the alpha threshold is swept (e.g., 0.01, 0.05, 0.10) to observe how the identified critical sample size shifts (See FR-004, Methodological Soundness).

## Assumptions

- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) is sufficient to complete [deferred] iterations per condition for sample sizes up to 500 within the 6-hour job limit, provided the R code is optimized for vectorization and avoids unnecessary object copying.
- The synthetic data generation assumes normal distributions for t-tests and ANOVA, and multinomial distributions for chi-squared tests, with no significant outliers or non-normality in the underlying population unless explicitly simulated.
- The "ground truth" for public small-sample datasets is not assumed to be known; instead, these datasets are used to generate bootstrapped power estimates and p-value distributions for comparison against the simulation, acknowledging that real-world data may contain unmeasured confounders.
- The analysis treats all findings as associational regarding the relationship between sample size and error rates, as the simulation design does not involve random assignment of sample sizes to experimental groups in a causal sense, but rather a systematic parameter sweep.
- The [deferred] iteration count is sufficient to stabilize error rate estimates within a margin of error of ±0.005 for the alpha level of 0.05, based on standard binomial variance approximations.
- The "reliability" threshold is defined strictly by the deviation of the Type I error rate from the nominal alpha (0.05) and the achievement of power ≥ 0.80, consistent with standard statistical power analysis conventions.