# Feature Specification: Exploring the Impact of Data Imputation Methods on Causal Inference

**Feature Branch**: `001-data-imputation-mnar-impact`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "How do different data imputation methods affect causal effect estimates under MNAR (Missing Not At Random) missingness mechanisms?"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation with Explicit MNAR Mechanisms (Priority: P1)

The system must generate synthetic structural causal models (SCM) with known ground-truth Average Treatment Effects (ATE) and explicitly parameterized Missing Not At Random (MNAR) mechanisms where missingness depends on the unobserved outcome values. **Note**: The 'ground truth' refers strictly to the parameter of the *generative model* defined in the simulation, not an external reality or recoverable causal effect from observed data, to avoid tautological validation.

**Why this priority**: This is the foundational step; without ground-truth data where the causal effect is known and the missingness mechanism is controlled, no bias quantification is possible. It enables the entire simulation study.

**Independent Test**: Can be fully tested by generating a dataset, verifying the ground-truth ATE matches the theoretical value defined in the SCM, and confirming the missingness pattern correlates with the outcome variable as specified by the MNAR parameter.

**Acceptance Scenarios**:

1. **Given** a defined structural causal model with treatment $T$, outcome $Y$, and confounders $X$, **When** the system generates 1,000 synthetic samples with an MNAR parameter $\beta=0.5$, **Then** the system must verify that the missingness indicator $M$ and the unobserved outcome values $Y$ exhibit a significant correlation (Spearman rank correlation coefficient $\rho > 0.5$ with $p < 0.01$).
2. **Given** the generated dataset, **When** the system calculates the ground-truth ATE using the complete data, **Then** the calculated ATE must match the theoretical ATE defined in the SCM within a tolerance of $< 0.01$.

---

### User Story 2 - Standard Imputation Pipeline Execution (Priority: P2)

The system must apply three standard imputation strategies (Mean, KNN, MICE) to the generated incomplete datasets, assuming MAR conditions, and subsequently estimate the ATE using Inverse Probability Weighting (IPW) and Propensity Score Matching (PSM). **Note**: The study measures the bias of the estimator relative to the *generative parameter*, acknowledging that under the defined MNAR mechanism, the true ATE is not identifiable from observed data alone.

**Why this priority**: This implements the core experimental manipulation—applying standard practices to non-standard (MNAR) data to observe the failure modes. It is the primary "test" of the research hypothesis.

**Independent Test**: Can be fully tested by running the imputation and estimation pipeline on a single generated dataset and verifying that output ATEs are produced for all three methods and two estimation techniques without runtime errors.

**Acceptance Scenarios**:

1. **Given** an incomplete dataset with missingness in $Y$ induced by a logistic model $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$, **When** the system applies Mean, KNN ($k=5$), and MICE imputation, **Then** the system must produce three complete datasets ready for causal analysis.
2. **Given** the three imputed datasets, **When** the system estimates the ATE using IPW and PSM, **Then** the system must output a matrix of 6 ATE estimates (3 methods $\times$ 2 estimators) per simulation run.

---

### User Story 3 - Bias Quantification and Sensitivity Analysis (Priority: P3)

The system must calculate the absolute bias and RMSE for each method across multiple replications, perform statistical significance testing (ANOVA/Friedman), and execute a sensitivity analysis sweeping the MNAR parameter $\beta$ to identify failure thresholds.

**Why this priority**: This delivers the final research output—the quantification of bias and the identification of where standard methods break down. It answers the research question directly.

**Independent Test**: Can be fully tested by running the analysis on a small batch (e.g., 10 runs) and verifying that bias metrics are calculated, statistical tests return p-values, and sensitivity plots show a monotonic trend in bias relative to $\beta$.

**Acceptance Scenarios**:

1. **Given** the results of 200 simulation runs across varying $\beta$ values, **When** the system calculates bias, **Then** the system must report the mean absolute bias and 95% confidence intervals for each imputation method.
2. **Given** the bias results, **When** the system performs a sensitivity analysis sweeping $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$, **Then** the system must output a dataset showing how the mean absolute bias changes at each step, confirming a monotonic trend defined by a Spearman rank correlation coefficient $\rho > 0.9$ and a p-value for trend $< 0.05$.

### Edge Cases

- What happens when the MNAR parameter $\beta$ is set to 0 (effectively MAR)? The system must correctly report that standard methods (MICE) perform well with near-zero bias, serving as the baseline control.
- How does the system handle extreme missingness (e.g., > 50% missing in $Y$)? The system must detect if the imputation fails to converge or produces infinite estimates and flag these runs as "failed" rather than including them in the bias average without explanation.
- What if the synthetic data generation produces a dataset with near-perfect collinearity between treatment and confounders? The system must include a collinearity diagnostic check and exclude or flag runs where VIF > 10 to prevent unstable ATE estimates.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate synthetic structural causal models with a binary treatment, continuous outcome, and confounders, ensuring the ground-truth ATE is known and explicitly stored. The system MUST explicitly document that this 'ground truth' is the parameter of the generative model, not an external reality (See US-1).
- **FR-002**: The system MUST inject missingness into the outcome variable $Y$ using a logistic model where $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$, allowing $\beta$ to control the strength of the MNAR mechanism. The system MUST acknowledge that under this mechanism, the true ATE is not identifiable from observed data alone, and the study measures bias relative to the generative parameter (See US-1, US-2).
- **FR-003**: The system MUST implement Mean, KNN ($k=5$), and MICE imputation algorithms that operate strictly on CPU without GPU acceleration (See US-2).
- **FR-004**: The system MUST estimate the ATE using both Inverse Probability Weighting (IPW) and Propensity Score Matching (PSM) on every imputed dataset (See US-2).
- **FR-005**: The system MUST calculate the absolute bias $|\hat{\tau}_{imp} - \tau_{true}|$ and RMSE for every simulation run and aggregate these across a sufficient number of replications to ensure statistical stability. (See US-3).
- **FR-006**: The system MUST perform a repeated-measures ANOVA or Friedman test to determine if the difference in bias across imputation methods is statistically significant ($p < 0.05$). The system MUST first run a Shapiro-Wilk test for normality on the bias distribution; if $p < 0.05$, it MUST use the Friedman test; otherwise, it MUST use Repeated-Measures ANOVA. Additionally, if the distribution is skewed, the system MUST compute bootstrap confidence intervals for the difference in medians as a robust alternative (See US-3).
- **FR-007**: The system MUST execute a sensitivity analysis sweeping the MNAR parameter $\beta$ over a range of values and report the resulting bias trends (See US-3).
- **FR-008**: The system MUST compute confidence interval coverage rates for the ATE estimates to assess validity under MNAR (See US-3).

### Key Entities

- **SyntheticDataset**: Represents a generated instance of the SCM with known ATE and injected missingness. Attributes: `ground_truth_ate`, `missingness_pattern`, `sample_size`.
- **ImputationResult**: Represents the output of an imputation method applied to a dataset. Attributes: `method_name`, `imputed_data`, `convergence_status`.
- **CausalEstimate**: Represents the final ATE calculation. Attributes: `imputation_method`, `estimator_type` (IPW/PSM), `estimated_ate`, `standard_error`, `bias`, `rmse`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The absolute bias of Mean imputation is measured against the ground-truth ATE and must show a statistically significant increase as the MNAR parameter $\beta$ increases from 0.0 to 1.0 (See FR-005, US-3).
- **SC-002**: The coverage rate of confidence intervals for MICE is measured against the nominal level and must drop significantly below this level as $\beta$ increases., defined by a statistically significant negative slope (p < 0.05) in the coverage-vs-beta regression (See FR-008, US-3).
- **SC-003**: The computational runtime for the full simulation (200 runs) is measured against the 6-hour GitHub Actions free-tier limit and must complete within 4 hours to ensure feasibility (See FR-003, US-2).
- **SC-004**: The statistical significance of the bias difference between methods is measured via p-value from the Friedman test (or ANOVA if normal) and must be $< 0.05$ for at least one comparison of MNAR strength (See FR-006, US-3).
- **SC-005**: The sensitivity analysis results are measured by the monotonicity of the bias curve across the $\beta$ sweep $\{0.0, 0.2, 0.5, 0.8, 1.0\}$, confirmed by a Spearman rank correlation coefficient $\rho > 0.9$ and p-value for trend $< 0.05$ (See FR-007, US-3).

## Assumptions

- The synthetic data generation using `causalinference` or `do-why` packages is computationally feasible on a standard CPU within a reasonable time limit for 200+ replications.
- The "standard" imputation methods (Mean, KNN, MICE) are implemented using `scikit-learn` and `statsmodels`/`fancyimpute` without requiring GPU acceleration or 8-bit quantization.
- The logistic missingness model $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$ is sufficient to model the MNAR mechanism for this study, and no more complex non-linear missingness functions are required for the initial scope.
- The ground-truth ATE is defined by the user in the simulation script (e.g., $\tau_{true} = 0.5$) and serves as the immutable reference for all bias calculations, acknowledging it is a parameter of the generative model.
- The sample size per simulation run (e.g., $N=1000$) is sufficient to provide stable ATE estimates while keeping memory usage under 7GB RAM.
- The sensitivity analysis threshold sweep is chosen based on community standards for exploring effect sizes in simulation studies, providing a concrete range to identify failure points.