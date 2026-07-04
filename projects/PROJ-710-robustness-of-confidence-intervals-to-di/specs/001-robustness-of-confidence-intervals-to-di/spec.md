# Feature Specification: Robustness of Confidence Intervals to Differential Privacy Noise

**Feature Branch**: `001-robustness-ci-dp-noise`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "How does the magnitude of differential‑privacy noise (controlled by the privacy budget ε) affect the frequentist coverage probability of confidence intervals for simple means and linear‑regression coefficients?"

## User Scenarios & Testing

### User Story 1 - Empirical Coverage Estimation under Varying Privacy Budgets (Priority: P1)

As a statistical analyst, I need to measure the empirical coverage probability of standard 95% confidence intervals for means and regression coefficients when data is perturbed by Laplace and Gaussian noise across a range of privacy budgets (ε), so that I can quantify the degradation of inferential validity as privacy guarantees tighten.

**Why this priority**: This is the core research question. Without establishing the baseline coverage degradation, no adjustments or conclusions can be drawn. It directly addresses the "phenomenon-vs-method" validation.

**Independent Test**: The system can be tested by running the simulation pipeline on a single dataset (e.g., UCI Adult) with a fixed set of ε values and noise types, outputting a CSV of coverage rates. The test verifies that the coverage rate is recorded and deviation from nominal is calculated.

**Acceptance Scenarios**:

1. **Given** a large synthetic population (N ≥ 1,000,000) with known parameters, **When** the system draws a sample, adds Laplace noise calibrated to ε=0.1, and computes 1,000 bootstrap 95% CIs, **Then** the system measures and records the empirical coverage rate and calculates the deviation from the nominal [deferred] target.
2. **Given** the same synthetic population, **When** the system adds Gaussian noise calibrated to ε=5.0 and computes 1,000 bootstrap 95% CIs, **Then** the system measures and records the empirical coverage rate and calculates the deviation from the nominal [deferred] target.
3. **Given** a linear regression target variable from the synthetic population, **When** the system perturbs predictors with DP noise and computes CIs for coefficients, **Then** the coverage rate is calculated and stored for the specific (ε, noise_type) combination.

---

### User Story 2 - Evaluation of Bias-Correction and Variance-Inflation Adjustments (Priority: P2)

As a methodologist, I need to apply unbiased estimators and variance-inflation corrections to the noisy data and re-evaluate the confidence interval coverage, so that I can determine if simple adjustments can restore nominal coverage for moderate privacy budgets.

**Why this priority**: This addresses the "expected results" and practical guidance aspect of the idea. It tests the hypothesis that adjustments can recover validity, which is the secondary value proposition.

**Independent Test**: The system can be tested by taking the noisy datasets from User Story 1, applying the specific correction formulas (e.g., from the 2021 Covington et al. paper), and comparing the new coverage rates against the unadjusted rates.

**Acceptance Scenarios**:

1. **Given** a dataset with Gaussian noise at ε=1.0, **When** the system applies the variance-inflation correction to the standard error estimate, **Then** the system measures the recalculated empirical coverage rate and compares it to the unadjusted rate to determine the improvement.
2. **Given** a dataset with Laplace noise at ε=0.5, **When** the system applies the unbiased estimator correction, **Then** the system measures the recalculated coverage rate and compares it to the nominal [deferred] target to document the delta.
3. **Given** the regression coefficients, **When** the system applies the bias-correction to the point estimate, **Then** the new coverage rate is computed and compared to the unadjusted rate in the results log.

---

### User Story 3 - Statistical Comparison and Visualization of Coverage Trends (Priority: P3)

As a researcher, I need to perform a Generalized Linear Model (GLM) with a binomial link to test the effects of ε and noise type on coverage, and generate plots comparing coverage vs. ε for all datasets and statistics, so that I can formally validate the systematic nature of the degradation.

**Why this priority**: This provides the statistical rigor required to claim a "systematic" effect rather than random noise. It synthesizes the results from the previous stories into a final conclusion.

**Independent Test**: The system can be tested by running the GLM script on the aggregated coverage data and generating the required plots. The test verifies that the GLM output includes p-values for the main effects and interaction.

**Acceptance Scenarios**:

1. **Given** the aggregated coverage data across all datasets, ε values, and noise types, **When** the system runs a GLM with binomial link, **Then** the system outputs the p-value for the "ε" factor.
2. **Given** the coverage data, **When** the system generates a line plot of coverage vs. ε, **Then** the plot clearly distinguishes between Laplace and Gaussian noise and includes error bars representing the standard error of the coverage estimate.
3. **Given** the results, **When** the system outputs a summary table, **Then** the table explicitly lists the coverage rate for each (dataset, statistic, ε, noise_type) combination.

### Edge Cases

- **What happens when** the sensitivity calculation results in a noise scale that exceeds the data range (e.g., very small ε on a small dataset)? The system must clamp the noise generation or log a warning that the data is effectively randomized, ensuring the CI calculation does not fail due to NaNs.
- **How does the system handle** datasets with collinear predictors in the regression step? The system must detect perfect collinearity, drop one predictor, and log the action, ensuring the regression coefficients are estimable.
- **What happens when** the bootstrap resample size equals the original dataset size but the original dataset is very small (n < 10)? The system must enforce a minimum sample size sufficient for the bootstrap to be statistically valid, or raise a specific error for that dataset.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic noisy datasets by adding calibrated Laplace and Gaussian noise to numeric attributes of UCI Adult, Iris, and Wine Quality datasets for a range of low to moderate privacy budgets (ε)., using a known global bound for sensitivity calibration (See US-1).
- **FR-002**: System MUST compute the "true" population parameters (means and OLS coefficients) from a large synthetic population (N ≥ 1,000,000) with known parameters to serve as the ground truth for coverage assessment (See US-1).
- **FR-003**: System MUST perform a sufficient number of bootstrap resamples for each noisy dataset to construct 95% confidence intervals for the target statistics (See US-1).
- **FR-004**: System MUST implement bias-correction and variance-inflation adjustments derived from recent literature and apply them to the noisy statistics before CI construction (See US-2).
- **FR-005**: System MUST execute a Generalized Linear Model (GLM) with a binomial link to test the statistical significance of the effects of ε and noise type on the empirical coverage probability (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis on the decision threshold for "acceptable coverage" (e.g., [deferred], [deferred], 95%) by sweeping the threshold and reporting the change in the count of datasets passing the criterion to ensure conclusions are robust to arbitrary threshold choices (See US-3).
- **FR-007**: System MUST ensure all statistical computations run on CPU-only hardware without GPU acceleration, fitting within 7 GB RAM and 6 hours of execution time (See Assumptions).
- **FR-008**: System MUST generate a large synthetic population (N ≥ 1,000,000) with known parameters for each dataset type to serve as the ground truth for coverage calculations, ensuring the ground truth is independent of the sample realization (See US-1).

### Key Entities

- **Dataset**: Represents the source data (Adult, Iris, Wine) with numeric attributes and a target variable.
- **NoiseProfile**: Represents a specific configuration of noise type (Laplace/Gaussian) and privacy budget (ε).
- **CoverageResult**: Represents the empirical coverage rate (0.0 to 1.0) for a specific combination of Dataset, NoiseProfile, Statistic (Mean/Regression), and AdjustmentMethod.
- **GroundTruth**: Represents the parameter values (mean, coefficient) calculated from the large synthetic population with known parameters.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Empirical coverage probability is measured against the nominal [deferred] target for each (ε, noise_type) combination to quantify degradation (See US-1).
- **SC-002**: The improvement in coverage probability is measured against the unadjusted baseline to evaluate the efficacy of bias-correction and variance-inflation methods (See US-2).
- **SC-003**: The statistical significance of the relationship between ε and coverage is measured against the null hypothesis of no effect using a GLM with binomial link (See US-3).
- **SC-004**: The computational feasibility is measured against the constraint of ≤ 6 hours total runtime on a standard GitHub Actions free-tier runner (See FR-007).
- **SC-005**: The robustness of the "acceptable coverage" conclusion is measured by sweeping the threshold (e.g., 90%, 93%, 95%) and reporting the variance in the number of successful cases (See FR-006).

## Assumptions

- The UCI Adult, Iris, and Wine Quality datasets are available via public URLs and can be downloaded without authentication or rate-limiting issues during the CI run.
- The "true" population parameters can be approximated with sufficient accuracy by calculating statistics on the full available sample of the public datasets, treating them as the population proxy, OR by generating a large synthetic population with known parameters as defined in FR-008.
- The sensitivity of the data attributes is estimated using a known global bound (e.g., [0, 1] for normalized data) for the purpose of calibrating the Laplace/Gaussian noise, ensuring the DP guarantee is not broken by data-dependent sensitivity.
- The standard multi-way ANOVA assumptions (normality of residuals, homogeneity of variance) are not met for coverage rates; therefore, a GLM with binomial link is used instead.
- The "bias-correction" and "variance-inflation" methods referenced in the related work (Covington et al., Karwa & Vadhan 2017) are applicable to the specific low-dimensional mean and regression models considered in this study.
- The GitHub Actions runner environment provides a standard recent Python environment. with `numpy`, `pandas`, `scipy`, and `statsmodels` pre-installed or installable within the time limit.
- The noise generation uses double-precision floating-point arithmetic to avoid precision errors that could distort the coverage calculation at very small ε.
- The dataset sizes are small enough that loading the full dataset into memory for a sufficient number of bootstrap iterations does not exceed the 7 GB RAM limit. (verified by the small size of Adult/Iris/Wine Quality).