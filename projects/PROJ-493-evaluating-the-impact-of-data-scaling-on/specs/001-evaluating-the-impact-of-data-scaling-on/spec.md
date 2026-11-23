# Feature Specification: Evaluating the Impact of Data Scaling on Statistical Test Sensitivity

**Feature Branch**: `001-data-scaling-sensitivity`  
**Created**: 2026-07-17  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Data Scaling on Statistical Test Sensitivity"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synthetic Data Generation and Ground Truth Establishment (Priority: P1)

The research pipeline MUST be able to generate synthetic datasets with strictly controlled distributional characteristics (skewness, kurtosis, outlier prevalence) where the true null hypothesis status is known with certainty. This allows for the precise measurement of Type I error rates without confounding factors from real-world data noise.

**Why this priority**: Without a ground-truth synthetic dataset where the null is exactly true, it is impossible to distinguish between a Type I error caused by the scaling method and one caused by inherent data structure. This is the foundational step for all subsequent sensitivity analysis.

**Independent Test**: The system generates a large number of synthetic datasets with a skewness of and [deferred] outlier prevalence across sample sizes n ∈ {20, 50, 100, 500}. A t-test is run on raw data; the observed Type I error rate (proportion of rejections at α=0.05) across ≥1,000 simulations must converge to the nominal 0.05 level within a 95% confidence interval, validating the simulation engine.

**Acceptance Scenarios**:

1. **Given** a target skewness of 2.0 and [deferred] outlier prevalence, **When** the system generates ≥1,000 synthetic datasets with a true null hypothesis across sample sizes n ∈ {20, 50, 100, 500}, **Then** the empirical Type I error rate of the untransformed t-test must be measured against the nominal α=0.05 level with a tolerance defined in the implementation plan (e.g., ±0.01).
2. **Given** a target kurtosis of 6.0, **When** the system generates synthetic data, **Then** the calculated sample kurtosis must match the target within ±0.2.

---

### User Story 2 - Transformation Application and Hypothesis Testing Execution (Priority: P2)

The system MUST apply four specific scaling transformations (log with offset, Box-Cox, rank-based inverse normal, z-score) to the generated and real datasets, and subsequently execute paired t-tests, one-way ANOVAs, and one-way Chi-squared tests on the transformed data to record p-values and effect sizes.

**Why this priority**: This is the core experimental loop. It directly addresses the research question by creating the data required to compare how different scalings alter inferential statistics for the three test types specified in the research idea.

**Independent Test**: The pipeline processes a single synthetic dataset through all four transformations and runs the specified tests. The output must include a structured record of p-values, Cohen's d (for t-tests), eta-squared (for ANOVA), and effect size estimates (for Chi-squared) for every transformation-test combination.

**Acceptance Scenarios**:

1. **Given** a dataset with skewness > 1.5, **When** the log-transformation is applied, **Then** the system must record the change in skewness (Δskewness) and report the distribution of these changes across the dataset.
2. **Given** a dataset and a selected transformation, **When** a paired t-test is executed, **Then** the system must output the p-value, 95% confidence interval, and Cohen's d effect size.
3. **Given** a dataset and a selected transformation, **When** a one-way ANOVA is executed, **Then** the system must output the p-value, 95% confidence interval, and eta-squared effect size.
4. **Given** a dataset and a selected transformation, **When** a one-way Chi-squared test is executed, **Then** the system must output the p-value and the effect size estimate (e.g., Cramér's V).

---

### User Story 3 - Sensitivity Analysis and Threshold Justification Reporting (Priority: P3)

The system MUST perform a sensitivity analysis on the decision thresholds used to classify "meaningful" deviations in error rates and effect sizes, sweeping the cutoff over a defined range and reporting how the classification of results changes.

**Why this priority**: To ensure methodological soundness, the definition of a "significant impact" cannot be arbitrary. A sensitivity sweep proves that the conclusions regarding scaling effects are robust to reasonable variations in the decision boundary, satisfying the methodology panel's requirement for threshold justification.

**Independent Test**: The system evaluates the impact of scaling using three different deviation thresholds: a low value, a moderate value, and a high value. The output must report the percentage of datasets classified as "highly sensitive" for each threshold, demonstrating how the conclusion shifts.

**Acceptance Scenarios**:

1. **Given** the calculated deviation of Type I error rates from the nominal 0.05 level, **When** the sensitivity sweep is executed with thresholds {0.01, 0.05, 0.10}, **Then** the system must report the count and percentage of datasets exceeding each threshold.
2. **Given** a specific distribution characteristic (e.g., skewness = 3.0), **When** the sensitivity analysis is run, **Then** the output must explicitly state the threshold used and the rationale (e.g., "0.01 chosen as a conservative bound for Type I error inflation").

---

### Edge Cases

- **What happens when** the Box-Cox transformation fails to converge due to negative values or extreme skewness? The system must automatically fall back to the log-transformation with a constant offset and log this fallback event for the final report.
- **How does the system handle** datasets with zero variance in a group (preventing t-test calculation)? The system must skip the test for that specific group pair and record the reason as "Zero Variance" rather than crashing.
- **What happens when** the synthetic data generation parameters (e.g., extreme kurtosis) result in numerical overflow? The system must catch the exception, discard that specific simulation run, and regenerate it to ensure the sample size remains valid.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic datasets with user-specified skewness, kurtosis, and outlier prevalence where the null hypothesis is strictly true, run ≥1,000 independent simulations, and verify the empirical Type I error rate falls within the 95% confidence interval of the nominal α level (See US-1).
- **FR-002**: System MUST download and parse at least 15 real-world datasets from UCI or OpenML that exhibit varying distributional characteristics (See US-1, US-2, US-3).
- **FR-003**: System MUST apply four transformations (log, Box-Cox, rank-based inverse normal, z-score) to all datasets, handling negative values via offset where necessary (See US-2).
- **FR-004**: System MUST execute paired t-tests, one-way ANOVAs, and one-way Chi-squared tests on all transformed datasets and record p-values, 95% CIs, and effect sizes (Cohen's d, eta-squared, Cramér's V) (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis sweeping the deviation threshold over {0.01, 0.05, 0.10} to report the stability of "high sensitivity" classifications (See US-3).
- **FR-006**: System MUST apply Benjamini-Hochberg correction to the p-values generated from the regression analysis of distribution metrics (FR-007), but NOT to the descriptive comparison of test statistics across transformations (See US-2).
- **FR-007**: IF the system performs a regression analysis on distribution metrics (e.g., skewness, kurtosis) to explain error rates, THEN it MUST calculate and report the Variance Inflation Factor (VIF) for all predictors. If VIF > 5 is detected, the system MUST flag this limitation in the report or apply Principal Component Analysis (PCA) to the predictors before regression (See US-3).

### Key Entities

- **Dataset**: Represents a collection of data points with attributes for source (UCI/OpenML/Synthetic), skewness, kurtosis, and outlier prevalence.
- **Transformation**: Represents a specific scaling method (Log, Box-Cox, Rank, Z-score) applied to a Dataset.
- **TestResult**: Represents the output of a hypothesis test, containing p-value, effect size, confidence interval, and the transformation used.
- **SensitivityReport**: Represents the output of the threshold sweep, mapping thresholds to counts of significant deviations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* is measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The empirical Type I error rate of the untransformed t-test on synthetic null data is measured against the nominal α=0.05 level to validate the simulation engine (See US-1, FR-001).
- **SC-002**: The deviation of empirical Type I error rates from 0.05 is measured across all four transformations to quantify the impact of scaling (See US-2, FR-004).
- **SC-003**: The magnitude of effect size distortion (Cohen's d, eta-squared, Cramér's V) is measured between raw and transformed data to assess practical significance (See US-2, FR-004).
- **SC-004**: The stability of "high sensitivity" classifications is measured against the three swept thresholds (0.01, 0.05, 0.10); the classification count for "high sensitivity" must remain within ±10% across the thresholds (See US-3, FR-005).
- **SC-005**: The computational execution time is measured against the 6-hour limit of the GitHub Actions free-tier runner to ensure feasibility (See Assumptions).
- **SC-006**: The variance inflation factor (VIF) is measured for predictors in the regression analysis to ensure collinearity does not invalidate the model (See US-3, FR-007).

## Assumptions

- **Assumption about data**: The UCI and OpenML repositories contain at least 15 datasets with sufficient variance and documented distributional properties to support the analysis of skewness and kurtosis effects.
- **Assumption about compute**: The entire analysis (15 real datasets + 1,000 synthetic simulations) will complete within 6 hours on a 2-core CPU with 7GB RAM using vectorized NumPy/SciPy operations and sampled subsets where necessary.
- **Assumption about method**: The Box-Cox transformation will be applied with a small constant offset (e.g., +1) for non-positive values, assuming this preserves the distributional shape sufficiently for the sensitivity analysis.
- **Assumption about inference**: Since the study uses observational data characteristics (skewness, kurtosis) and synthetic generation rather than randomized intervention on the data itself, all findings regarding scaling effects will be framed as associational, not causal, regarding the data generation process.
- **Assumption about thresholds**: A deviation of 0.01 from the nominal 0.05 Type I error rate is a defensible community-standard baseline for "meaningful" inflation, based on standard statistical practice for error control.