# Feature Specification: Estimating Causal Effects with Doubly Robust Methods on Observational Data

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-08-10  
**Status**: Draft  
**Input**: User description: "Estimating Causal Effects with Doubly Robust Methods on Observational Data"

## User Scenarios & Testing

### User Story 1 - Simulation Environment with Known Ground Truth (Priority: P1)

The researcher MUST be able to generate a synthetic observational dataset with a predefined, known non-linear data generating process (DGP) where the true Average Treatment Effect (ATE) is explicitly calculable. This environment allows for the isolation of model misspecification effects by comparing estimates against a known truth.

**Why this priority**: Without a controlled environment where the ground truth is known, it is impossible to quantify bias or validate the "doubly robust" property under dual misspecification. This is the foundational step for all subsequent analysis.

**Independent Test**: The system can be tested by running a simulation with a simple linear DGP and verifying that a correctly specified linear model recovers the true ATE with bias < 0.01, confirming the simulation engine's correctness before introducing complexity.

**Acceptance Scenarios**:

1. **Given** a defined non-linear DGP (e.g., $Y = \sin(X_1) + X_2^2 + \epsilon$) and a known propensity function, **When** the simulation generates $N=1000$ samples, **Then** the calculated true ATE matches the theoretical expectation within a tolerance of 0.001.
2. **Given** the simulation parameters, **When** the random seed is fixed, **Then** the generated dataset is identical across repeated runs, ensuring reproducibility.

---

### User Story 2 - Grid of Model Misspecifications and AIPW Estimation (Priority: P2)

The researcher MUST be able to configure and execute a grid of model misspecifications (varying outcome and propensity model complexities) and compute the Augmented Inverse Probability Weighting (AIPW) estimator for each configuration. This enables the systematic exploration of how different error combinations affect bias.

**Why this priority**: This is the core experimental mechanism. It directly addresses the research question by allowing the comparison of linear vs. non-linear model mismatches.

**Independent Test**: The system can be tested by running a 2x2 grid (Linear Outcome/Linear Propensity vs. Misspecified Outcome/Misspecified Propensity) and verifying that the "Double Robust" condition holds (i.e., when one is correct, bias is near zero) while dual misspecification yields non-zero bias.

**Acceptance Scenarios**:

1. **Given** a grid of 3 outcome models and 3 propensity models, **When** the AIPW estimator is run for all 9 combinations, **Then** the system outputs a table of estimated ATEs and calculated biases for each combination.
2. **Given** a scenario where the outcome model is correctly specified but the propensity model is misspecified, **When** the ATE is estimated, **Then** the bias is statistically indistinguishable from zero (|bias| < 0.05).

---

### User Story 3 - Meta-Regression and Bias Amplification Analysis (Priority: P3)

The researcher MUST be able to perform a meta-regression (ANOVA-style) on the simulation results to isolate the interaction term between outcome and propensity misspecification types, and visualize the results as heatmaps. This identifies specific "danger zones" of non-linear error amplification.

**Why this priority**: This transforms raw simulation data into the specific scientific insight required by the research question: identifying *structural* interactions that amplify bias.

**Independent Test**: The system can be tested by feeding it simulation results where the interaction effect is known to be zero (by construction) and verifying that the meta-regression coefficient for the interaction term is not significantly different from zero (p > 0.05).

**Acceptance Scenarios**:

1. **Given** the full set of simulation results across the misspecification grid, **When** the meta-regression is executed, **Then** the output includes the coefficient and p-value for the interaction term between outcome and propensity misspecification types.
2. **Given** the bias data, **When** the heatmap is generated, **Then** the visualization clearly displays bias magnitude across the grid, with distinct regions of high bias (> 0.1) highlighted.

### Edge Cases

- **What happens when** the propensity score estimates are exactly 0 or 1 (perfect separation)? The system MUST clip propensity scores to a safe range (e.g., a bounded interval strictly within the unit interval) to prevent division by zero in the IPW component.
- **How does system handle** extremely high-dimensional covariates that exceed memory limits? The system MUST implement a sample subsetting strategy or dimensionality reduction (e.g., PCA) to ensure the data fits within the 7 GB RAM constraint.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic datasets with known non-linear ground truth relationships for covariates, treatment, and outcome, ensuring the true ATE is computable (See US-1).
- **FR-002**: System MUST implement an AIPW estimator that accepts user-defined functional forms for both the outcome model (e.g., linear, polynomial) and the propensity model (e.g., logistic, interaction-heavy) (See US-2).
- **FR-003**: System MUST execute a simulation loop of at least 1,000 Monte Carlo replications for each configuration in the misspecification grid to ensure statistical stability (See US-2).
- **FR-004**: System MUST calculate the bias as the absolute difference between the estimated ATE and the true ATE for every replication and aggregate results by configuration (See US-2).
- **FR-005**: System MUST perform a meta-regression analysis on the aggregated bias results to isolate the interaction effect between outcome and propensity model misspecification types (See US-3).
- **FR-006**: System MUST generate visualizations (heatmaps) mapping bias magnitude against the grid of functional form mismatches (See US-3).

### Key Entities

- **SimulationConfig**: Defines the DGP parameters, sample size, seed, and the specific combination of outcome/propensity model types to test.
- **EstimationResult**: Stores the estimated ATE, calculated bias, confidence interval coverage, and metadata for a single replication.
- **AggregatedMetrics**: Contains the mean bias, standard error, and meta-regression coefficients for a specific grid configuration.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of simulations where the correctly specified model (either outcome or propensity) yields a bias < 0.05 is measured against the theoretical expectation of [deferred] consistency (See US-2).
- **SC-002**: The coefficient of the interaction term in the meta-regression is measured against a null hypothesis of zero to determine if bias amplification is statistically significant (See US-3).
- **SC-003**: The empirical coverage probability of the 95% confidence intervals under dual misspecification is measured against the nominal [deferred] level to assess validity degradation (See US-3).
- **SC-004**: The maximum memory usage during the simulation loop is measured against the available RAM constraint to ensure feasibility on free-tier runners (See Assumptions).

## Assumptions

- The synthetic data generation uses `pyDOE2` or similar standard libraries to create high-dimensional covariates with known non-linear relationships (e.g., sine, quadratic) as specified in the methodology sketch.
- The AIPW implementation relies on `statsmodels` or `causalml` running in CPU-only mode with default precision, avoiding any GPU-specific libraries (e.g., `torch.cuda`, `bitsandbytes`).
- The sample size $N$ is capped at a value sufficient to ensure the total compute time for 1,000 replications across the grid does not exceed the 6-hour GitHub Actions limit.
- Propensity scores are clipped to the interval $[0.01, 0.99]$ to prevent numerical instability in the inverse probability weighting step.
- The meta-regression treats the misspecification types as categorical factors to isolate interaction effects.
- The study is purely observational (simulated); no causal claims are made about real-world populations, only about the behavior of the estimator under the defined DGP.
