# Feature Specification: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Feature Branch**: `001-statistical-properties-of-integer-partitions-into-distinct-prime-summands`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "How does the asymptotic growth rate of the partition function $p_{\mathcal{P}}(n)$ (counting partitions of $n$ into distinct primes) deviate from the predictions of Meinardus' theorem when applied to the prime set, and can these deviations be modeled as a systematic correction term dependent on the prime density?"

## User Scenarios & Testing

### User Story 1 - Compute Exact Partition Values and Asymptotic Baseline (Priority: P1)

As a researcher, I need to compute the exact values of $p_{\mathcal{P}}(n)$ for all integers $n$ from 1 to [deferred] and generate the corresponding theoretical asymptotic values $Q_{as}(n)$ derived from the distinct-partition variant of Meinardus' theorem, so that I can establish the ground truth and the baseline prediction for the error analysis.

**Why this priority**: This is the foundational data generation step. Without accurate exact counts and the theoretical baseline, no error analysis or modeling can occur. It represents the core "data" of the study.

**Independent Test**: This can be fully tested by running the computation script and verifying that the output file contains [deferred] rows where the first column is $n$, the second is $p_{\mathcal{P}}(n)$, and the third is $Q_{as}(n)$, with $p_{\mathcal{P}}(n) > 0$ for all $n$ and $Q_{as}(n)$ matching the formula for distinct parts.

**Acceptance Scenarios**:

1. **Given** a clean Python environment with `numpy` and `math`, **When** the dynamic programming script is executed for $n_{max}=50,000$, **Then** the output CSV contains [deferred] rows with non-negative integer counts for $p_{\mathcal{P}}(n)$ and positive float values for $Q_{as}(n)$.
2. **Given** the computed values, **When** an automated comparison is performed against a pre-computed reference file of the first 100 values, **Then** the computed counts match the reference values with exact integer match.

---

### User Story 2 - Calculate and Model Residual Error with Density Features (Priority: P2)

As a researcher, I need to calculate the log-residuals $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$ and fit a statistical model (linear regression or GAM) using prime density features ($\pi(n)$, $1/\ln(n)$, and distance to nearest prime) as predictors, so that I can quantify the systematic bias and determine if prime density explains the deviation. This tests for higher-order correction terms not captured by the leading-order density dependence of the baseline.

**Why this priority**: This addresses the primary research question directly. It transforms raw data into the specific insight (systematic bias vs. random noise) required to validate or refute the hypothesis.

**Independent Test**: This can be tested by running the modeling script and checking that the output includes a regression summary with coefficients for the density features, an $R^2$ score, and a plot of residuals vs. fitted values.

**Acceptance Scenarios**:

1. **Given** the dataset of $n$, $p_{\mathcal{P}}(n)$, and $Q_{as}(n)$, **When** the residual calculation and feature engineering script runs, **Then** the resulting dataset contains the column $R(n)$ and the derived density predictors, and the regression model outputs a coefficient for $1/\ln(n)$ that is not `NaN`.
2. **Given** the fitted model, **When** a t-test is performed on the density coefficients, **Then** the output includes a p-value for each coefficient, allowing the researcher to determine statistical significance (e.g., $p < 0.05$).

---

### User Story 3 - Validate Model Robustness and Visualize Convergence (Priority: P3)

As a researcher, I need to perform cross-validation (10-fold) on the regression model and generate visualizations comparing the raw residuals against the fitted correction term, so that I can assess the model's generalizability and visually inspect the convergence behavior for anomalies.

**Why this priority**: This ensures the findings are not overfitted to the specific sample and provides the necessary visual evidence for the final report. It confirms the reliability of the "systematic bias" claim.

**Independent Test**: This can be tested by running the validation script and verifying that the cross-validation error (MSE) is reported for each fold and that a PNG/PDF plot is generated showing the residual trend.

**Acceptance Scenarios**:

1. **Given** the fitted regression model, **When** 10-fold cross-validation is executed, **Then** the output reports the Mean Squared Error (MSE) for each of the 10 folds and the mean MSE across all folds.
2. **Given** the model results, **When** the visualization script runs, **Then** it produces a plot with $n$ on the x-axis, showing both the raw residuals $R(n)$ and the predicted correction term, allowing visual identification of periodic anomalies.

---

### Edge Cases

- **What happens when** $n$ is small (e.g., $n < 5$) where no partitions into distinct primes exist? The system must handle $p_{\mathcal{P}}(n) = 0$ gracefully, likely by excluding these from log-residual calculations or handling the log(0) case explicitly (e.g., setting residual to a specific marker or skipping).
- **How does system handle** the computational limits of the dynamic programming array? The system must use a sparse array or bitset optimization to ensure the full iteration range up to n_max=50,000 fits within the 7 GB RAM limit of the CI runner.
- **What happens when** the asymptotic formula $Q_{as}(n)$ yields a value extremely close to zero or negative due to numerical precision errors? The system must clamp $Q_{as}(n)$ to a minimum positive value (e.g., $10^{-10}$) before taking the logarithm to prevent domain errors.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the exact count of partitions of $n$ into distinct primes, $p_{\mathcal{P}}(n)$, for all integers $1 \le n \le [deferred]$ using a dynamic programming approach with memory optimization to fit within ~7 GB RAM. (See US-1)
- **FR-002**: System MUST implement the asymptotic formula $Q_{as}(n)$ based on the distinct-partition variant of Meinardus' theorem (using the generating function $\prod (1+q^p)$) to generate theoretical predictions for the same range $1 \le n \le [deferred]$. (See US-1)
- **FR-003**: System MUST calculate the log-residual $R(n) = \log(p_{\mathcal{P}}(n)) - \log(Q_{as}(n))$ for all $n$ where $p_{\mathcal{P}}(n) > 0$ and $Q_{as}(n) > 0$, handling edge cases where values are zero or non-positive. (See US-2)
- **FR-004**: System MUST generate predictor variables including the prime-counting function $\pi(n)$, the prime density $1/\ln(n)$, and the distance to the nearest prime (absolute difference to the closest prime, either smaller or larger), ensuring these are derived independently of the partition calculation. This feature is essential to distinguish local fluctuations from global trends. (See US-2)
- **FR-005**: System MUST fit a linear regression or Generalized Additive Model (GAM) where $R(n)$ is the dependent variable and the density metrics are independent variables, including sine/cosine terms based on $\log n$ to account for potential oscillatory components, and outputting coefficients, p-values, and $R^2$. (See US-2)
- **FR-006**: System MUST perform 10-fold cross-validation on the regression model to estimate the Mean Squared Error (MSE) on held-out data, ensuring the model generalizes beyond the training set. (See US-3)
- **FR-007**: System MUST generate a visualization plotting $n$ against the raw residuals $R(n)$ and the fitted correction term to visually inspect convergence and identify periodic anomalies. (See US-3)
- **FR-008**: System MUST include a null model (intercept-only) in the regression analysis to verify that the observed correlation is not an artifact of the baseline's density dependence. (See US-2)

### Key Entities

- **PartitionRecord**: Represents a single data point containing $n$, $p_{\mathcal{P}}(n)$, $Q_{as}(n)$, and the calculated $R(n)$.
- **DensityFeatureSet**: Represents the independent variables for a given $n$, including $\pi(n)$, $1/\ln(n)$, and nearest prime distance (absolute difference to the closest prime).
- **RegressionModel**: Represents the fitted statistical model, storing coefficients, intercept, and performance metrics ($R^2$, MSE).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The residual analysis must demonstrate a statistically significant correlation (p-value < 0.05) between the log-residuals $R(n)$ and at least one prime density predictor (e.g., $1/\ln(n)$), measured against the null hypothesis of zero correlation. (See US-2)
- **SC-002**: The regression model must achieve an $R^2$ value of at least 0.05 on the 10-fold cross-validation, measured against the baseline of a null model with no predictors. (See US-3)
- **SC-003**: The computed values $p_{\mathcal{P}}(n)$ must match known small-case enumerations (e.g., $n=5, 6, 10$) with exact integer match, measured against pre-computed reference values for $n \le 100$. (See US-1)
- **SC-004**: The entire data generation and analysis pipeline must complete within 6 hours on a standard GitHub Actions free-tier runner (2 CPU, 7 GB RAM), measured against the job timeout limit. (See US-1, US-2, US-3)
- **SC-005**: If multiple hypothesis tests are performed (e.g., testing multiple density predictors), the system MUST apply a Bonferroni or Benjamini-Hochberg correction to the p-values, measured against the standard false discovery rate control methods. (See US-2)
- **SC-006**: Peak memory usage of the dynamic programming algorithm must be $\le 6.5$ GB, measured against the system resource monitor. (See US-1)

## Assumptions

- **Assumption about data**: The dataset of primes up to 50,000 is finite and can be pre-computed or generated on-the-fly within the memory constraints of the CI runner.
- **Assumption about methodology**: The applicability of the asymptotic formula $Q_{as}(n)$ for distinct parts to the finite range $n \le [deferred]$ is a hypothesis to be tested (i.e., we assume the leading order term dominates at $n=50,000$).
- **Assumption about computational resources**: The dynamic programming algorithm for $p_{\mathcal{P}}(n)$ can be optimized (e.g., using a 1D array or bitset) to fit within the 7 GB RAM limit of the GitHub Actions free tier without requiring GPU acceleration.
- **Assumption about error nature**: The deviation between $p_{\mathcal{P}}(n)$ and $Q_{as}(n)$ is expected to be systematic and correlated with prime density, rather than purely random noise, justifying the regression approach.
- **Assumption about statistical validity**: The sample size of [deferred] data points is sufficient to detect a meaningful correlation between the residuals and density features, even if the effect size is small.
- **Assumption about threshold justification**: Any decision cutoffs used in the regression (e.g., significance level $\alpha=0.05$) are standard community defaults and do not require sensitivity analysis in this exploratory context, as the primary goal is detection of *any* signal.