# Feature Specification: Quantifying Uncertainty in Small Sample Regression Models

**Feature Branch**: `001-quantify-uncertainty-small-sample`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How do Bayesian regression with weakly informative priors compare to frequentist bootstrap resampling in maintaining nominal coverage probabilities for parameter estimates when $N < 50$ and predictors are collinear?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Simulation Engine for Coverage Probability Estimation (Priority: P1)

The researcher needs to generate synthetic datasets with controlled sample sizes ($N < 50$) and specific correlation structures between predictors to empirically test how often confidence/credible intervals capture the true parameter value.

**Why this priority**: This is the core mechanism of the research. Without the ability to simulate data with known ground truth parameters and controlled collinearity, the comparison between Bayesian and Bootstrap methods cannot be performed. It delivers the primary value: the raw data for the study.

**Independent Test**: Can be fully tested by running a single simulation batch with fixed random seeds and verifying that the generated data matrices have the requested correlation coefficients and that the known true parameters are stored in the metadata.

**Acceptance Scenarios**:

1. **Given** a configuration for $N=30$ and a correlation matrix with $\rho=0.85$, **When** the simulation engine generates 100 datasets, **Then** the empirical correlation of the generated predictors matches the target $\rho$ within a tolerance of $\pm 0.02$ across the aggregate of the 100 datasets, and the true regression coefficients are recorded for every dataset.
2. **Given** a configuration for $N=45$ with no collinearity, **When** the simulation engine generates data, **Then** the generated predictor matrix is full rank, and the system outputs a summary of the true parameter values used for verification.

---

### User Story 2 - Comparative Uncertainty Quantification Pipeline (Priority: P2)

The researcher needs to run three distinct modeling approaches (OLS, Non-parametric Bootstrap, Bayesian Regression with weakly informative priors) on the simulated datasets and calculate the empirical coverage probability for each.

**Why this priority**: This implements the specific research question (Bayesian vs. Bootstrap vs. OLS). It transforms raw simulated data into the comparative metric (coverage probability) required for the study's conclusions.

**Independent Test**: Can be tested by feeding a single pre-generated dataset with known parameters into the pipeline and verifying that all three methods produce interval estimates and that the "True Parameter" falls within the generated interval for each method (or not) as a binary flag for this instance.

**Acceptance Scenarios**:

1. **Given** a dataset with known true coefficients $\beta_{true}$, **When** the pipeline runs OLS, Bootstrap (defaulting to 500 resamples), and Bayesian regression (4 chains, 2000 samples), **Then** the system outputs three distinct interval estimates and a binary flag indicating whether $\beta_{true}$ is contained in the generated interval for each method.
2. **Given** a high-collinearity scenario, **When** the pipeline executes, **Then** the Bayesian method completes without divergent transitions exceeding 1% of the total 8000 samples (4 chains × 2000 samples), and the Bootstrap method completes within 10 seconds per dataset.

---

### User Story 3 - Real-World Validation on UCI Dataset (Priority: P3)

The researcher needs to apply the selected best-performing method (from the simulation) to a real-world small-sample dataset (e.g., UCI Concrete Compressive Strength) to confirm that the simulation findings hold in practice.

**Why this priority**: This provides external validity to the simulation results. While the simulation proves the statistical property, the real-world check ensures the methods behave reasonably on actual messy data, adding robustness to the final paper.

**Independent Test**: Can be tested by loading the UCI Concrete dataset, subsampling to $N<50$, running the chosen method, and verifying that the output includes interval stability metrics, width comparison, and diagnostic plots (since ground truth is unavailable).

**Acceptance Scenarios**:

1. **Given** the UCI Concrete dataset, **When** the system subsamples to $N=40$ and runs the Bayesian model, **Then** the output includes a 95% credible interval for the regression coefficients and a diagnostic plot showing the posterior distribution.
2. **Given** the same dataset, **When** the system compares the interval widths of the Bayesian model vs. OLS, **Then** the system reports the ratio of interval widths.

### Edge Cases

- What happens when the generated correlation matrix is not positive semi-definite? (System must detect and regenerate or adjust the matrix).
- How does the system handle cases where the Bayesian sampler fails to converge (R-hat > 1.05) in a specific simulation run? (System must flag the run as "invalid" and exclude it from the final coverage calculation, logging the failure).
- How does the system handle the boundary condition where $N$ is extremely small (e.g., $N=5$)? (System must ensure the regression is mathematically solvable; if predictors > $N-1$, the simulation must skip that configuration and log a "rank-deficient" warning).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate synthetic regression datasets with user-specified sample sizes ($3 \le N \le 49$) and a target correlation matrix for predictors, ensuring the ground truth parameters are stored for coverage calculation (See US-1).
- **FR-002**: The system MUST implement a Non-parametric Bootstrap procedure with a configurable number of resamples per dataset, defaulting to 500, to generate frequentist confidence intervals (See US-2).
- **FR-003**: The system MUST implement a Bayesian Linear Regression model using weakly informative priors (e.g., Normal(0, 10) for slopes, Half-Cauchy for scale) with 4 chains and 2000 samples per chain, discarding the first 500 as warm-up (See US-2).
- **FR-004**: The system MUST calculate the empirical coverage probability for each method by comparing the generated 95% confidence/credible intervals against the known true parameters across 200 Monte Carlo replications (See US-2).
- **FR-005**: The system MUST validate the methods on a real-world UCI dataset with $N < 50$ and at least 3 predictors (default: Concrete Compressive Strength) by subsampling and generating interval estimates without fine-tuning hyperparameters, focusing on interval stability and width comparison (See US-3).
- **FR-006**: The system MUST perform a collinearity diagnostic (Variance Inflation Factor) on all generated datasets and flag any where VIF > 10 to ensure the "high collinearity" condition is met (See US-1, US-2).
- **FR-007**: The system MUST output calibration plots comparing interval width vs. coverage probability for all three methods (See US-2, US-3).

### Key Entities

- **SimulationConfig**: Defines $N$, number of predictors, correlation matrix, noise level, and true coefficients.
- **DatasetInstance**: A single realization of data with attributes: $X$ (matrix), $y$ (vector), $\beta_{true}$ (vector).
- **IntervalResult**: Contains the lower/upper bounds for OLS, Bootstrap, and Bayesian methods, and the binary "covered" status for each.
- **CoverageMetric**: Aggregated statistics: empirical coverage rate, average interval width, and standard error of the coverage estimate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The empirical coverage probability for the Bayesian method is measured against the nominal [deferred] level to determine if it is within the acceptable Monte Carlo error margin (See FR-004).
- **SC-002**: The empirical coverage probability for the OLS method is measured against the nominal [deferred] level to quantify the degree of anti-conservatism (under-coverage) (See FR-004).
- **SC-003**: The average interval width of the Bootstrap method is measured against the Bayesian method to assess the efficiency trade-off (See FR-004, FR-007).
- **SC-004**: The system MUST complete 200 simulation runs within 6 hours on standard GitHub Actions runner (See FR-002, FR-003).
- **SC-005**: The convergence rate (percentage of chains with R-hat < 1.05) for the Bayesian model is measured against a 99% success threshold to ensure methodological validity (See FR-003).

## Assumptions

- The UCI Machine Learning Repository contains at least one dataset with sufficient features to allow for a subsample of $N < 50$ with at least 3 predictors, ensuring the regression is not trivially under-determined.
- The "weakly informative priors" defined as Normal(0, 10) for coefficients and Half-Cauchy(0, 2.5) for the noise scale are appropriate community standards for this specific comparison and do not require further justification in the study design.
- The GitHub Actions free-tier runner (2 CPU, 7GB RAM) is sufficient to run 200 Monte Carlo replications with 500 bootstrap samples and 2000 MCMC samples per chain within the 6-hour job limit, provided no GPU is requested.
- The correlation structures generated in the synthetic data will be stable and positive semi-definite without requiring complex matrix adjustment algorithms beyond standard Cholesky decomposition.
- The real-world validation on the UCI dataset will treat the "true parameters" as unknown; therefore, the validation step focuses on interval stability and width comparison rather than coverage calculation (since ground truth is unavailable).
- The collinearity introduced in the synthetic data will be strong enough (VIF > 10) to trigger the expected degradation in OLS performance, as hypothesized in the motivation.
- A sufficient number of Monte Carlo replications is selected to balance statistical power (standard error within a target precision range for [deferred] coverage) with the 6-hour runtime constraint., acknowledging that larger replications would be ideal but are infeasible on the free tier.
- The default resample count of 500 for Bootstrap and 2000 MCMC samples per chain are sufficient to produce stable interval estimates for small $N$, based on community standards for similar simulation studies.