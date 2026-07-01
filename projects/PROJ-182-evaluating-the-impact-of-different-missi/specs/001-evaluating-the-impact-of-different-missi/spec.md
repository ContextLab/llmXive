# Feature Specification: Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs

**Feature Branch**: `001-evaluating-missing-data-rd`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs"

## User Scenarios & Testing

### User Story 1 - Simulate RD Data with Controlled Missingness (Priority: P1)

The system must generate synthetic Regression Discontinuity (RD) datasets and introduce missing data under three distinct mechanisms (MCAR, MAR, MNAR) at varying rates to enable controlled experimentation.

**Why this priority**: This is the foundational step. Without valid, reproducible synthetic data that accurately reflects the theoretical properties of MCAR, MAR, and MNAR, no subsequent estimation or evaluation can occur. It delivers the necessary input for the entire research pipeline.

**Independent Test**: Can be fully tested by running the data generation script with fixed random seeds and verifying that the missingness patterns statistically match the intended mechanism definitions (e.g., missingness in MAR correlates with observed covariates but not the outcome; MNAR correlates with the outcome).

**Acceptance Scenarios**:

1. **Given** a defined RD simulation model (running variable, outcome, covariates), **When** the system applies an MCAR mechanism at a [deferred] missingness rate, **Then** the missingness indicator is statistically independent of both observed and unobserved variables, verified by a Chi-square test (p > 0.05).
2. **Given** a defined RD simulation model, **When** the system applies an MAR mechanism dependent on a specific covariate, **Then** the missingness indicator is significantly correlated with that covariate but not the outcome variable, verified by Pearson correlation (|r| > 0.1, p < 0.05).
3. **Given** a defined RD simulation model, **When** the system applies an MNAR mechanism dependent on the outcome, **Then** the correlation between the missingness mask and the *generated* (ground truth) outcome values is |r| > 0.5, confirming the generation code matches the definition (See FR-002).

---

### User Story 2 - Execute RD Estimators with Correction Strategies (Priority: P2)

The system must apply four distinct estimation procedures (Naïve Local-Linear, Multiple Imputation, Inverse-Probability Weighting, Selection-Model Correction) to the generated datasets and compute point estimates and standard errors for each. Note: IPW is included as a baseline to demonstrate failure under MNAR conditions.

**Why this priority**: This delivers the core analytical engine. It transforms the prepared data into quantitative results, allowing for the comparison of estimator performance under different conditions.

**Independent Test**: Can be fully tested by running the estimation pipeline on a small subset of data and verifying that the output includes bias-corrected estimates where applicable and that the code handles the specific missingness flags without crashing.

**Acceptance Scenarios**:

1. **Given** a dataset with [deferred] MAR missingness, **When** the Multiple Imputation (5 imputations) estimator is applied, **Then** the system produces a pooled RD estimate and standard error using Rubin's rules.
2. **Given** a dataset with [deferred] MCAR missingness, **When** the Inverse-Probability Weighting (IPW) estimator is applied, **Then** the system produces an RD estimate weighted by the inverse of the estimated propensity score.
3. **Given** a dataset with MNAR missingness, **When** the Selection-Model (Heckman-type) estimator is applied, **Then** the system attempts to fit the joint model; if it converges within 50 iterations, it outputs a bias-adjusted estimate; otherwise, it logs a specific error code and returns NaN (See FR-008).

---

### User Story 3 - Aggregate Monte-Carlo Metrics and Visualize Results (Priority: P3)

The system must run a sufficient number of Monte-Carlo replications for each configuration, aggregate performance metrics (Bias, RMSE, 95% CI Coverage), and generate summary tables and heatmaps.

**Why this priority**: This provides the final research output. It synthesizes the raw estimation results into interpretable evidence regarding the robustness of RD designs under missing data.

**Independent Test**: Can be fully tested by running a reduced replication count (e.g., 10) and verifying that the output files (CSV/JSON) contain the correct columns (Bias, RMSE, Coverage) and that the visualization script generates a heatmap without errors.

**Acceptance Scenarios**:

1. **Given** 1,000 replication results for a specific mechanism and estimator, **When** the aggregation step runs, **Then** the system calculates the mean Bias, Root-Mean-Square Error (RMSE), and empirical 95% Confidence Interval coverage rate.
2. **Given** aggregated metrics across all mechanisms and estimators, **When** the visualization step runs, **Then** the system generates a heatmap showing Bias and Coverage rates across missingness mechanisms.
3. **Given** the full simulation output, **When** the results are compared, **Then** the system identifies the estimator with the lowest RMSE for each missingness mechanism.

---

### Edge Cases

- **What happens when** the missingness rate is [deferred]? The system should gracefully skip estimation for that configuration and log a warning rather than crashing with a division-by-zero error in IPW.
- **How does the system handle** convergence failures in the Heckman selection model? The system should catch the convergence error, record a NaN for the estimate, and continue with the next replication, ensuring the Monte-Carlo loop is not interrupted.
- **What happens when** the bandwidth selection rule (Imbens-Kalyanaraman) returns a value of 0 or negative due to extreme data sparsity? The system must enforce a minimum bandwidth floor of [deferred] of the running variable range to ensure the local regression is computable (See FR-003).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic RD data with a running variable, outcome, and covariates using a triangular kernel model, ensuring the true discontinuity effect is known and fixed. (See US-1)
- **FR-002**: System MUST implement three distinct missingness mechanisms (MCAR, MAR, MNAR) where MAR depends on observed covariates and MNAR depends on the unobserved outcome value. (See US-1)
- **FR-003**: System MUST apply a Naïve Local-Linear RD estimator using the Imbens-Kalyanaraman bandwidth selection rule, with a mandatory fallback to a fixed bandwidth of [deferred] of the running variable range if the IK rule returns a value < 5% or is non-positive, logging the switch. (See US-2)
- **FR-004**: System MUST implement Multiple Imputation using the `mice` logic (5 imputations) and apply Rubin's rules to pool estimates across imputed datasets. (See US-2)
- **FR-005**: System MUST implement Inverse-Probability Weighting (IPW) where weights are derived from a logistic regression model predicting the observation indicator, acknowledging this method is theoretically invalid for MNAR and included as a baseline failure case. (See US-2)
- **FR-006**: System MUST run a minimum of 1,000 Monte-Carlo replications for each combination of mechanism, missing rate, and estimator to ensure stable metric estimation. (See US-3)
- **FR-007**: System MUST compute and store Bias, RMSE, and empirical 95% Confidence Interval coverage rates for every replication. (See US-3)
- **FR-008**: System MUST implement a Selection-Model (Heckman-type) estimator that attempts to fit a joint model of outcome and missingness, converging within 50 iterations, and outputting a bias-adjusted estimate or NaN if it fails. (See US-2)

### Key Entities

- **SimulationConfig**: Defines the parameters for data generation, including the true discontinuity effect, sample size, and the specific missingness mechanism to apply.
- **MissingnessPattern**: A binary mask indicating which observations are missing for the outcome and/or covariates, generated based on the chosen mechanism.
- **EstimationResult**: The output of a single replication, containing the point estimate, standard error, and the specific method (Naïve, MI, IPW, Selection) used.
- **AggregatedMetric**: The summary statistics (Mean Bias, RMSE, Coverage) calculated across the 1,000 replications for a specific configuration.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The empirical 95% Confidence Interval coverage rate is measured against the nominal [deferred] level to assess estimator validity. (See FR-007)
- **SC-002**: The ratio of the estimator's RMSE to the RMSE of the Naïve estimator on 100% complete synthetic data is measured to quantify efficiency loss. (See FR-007)
- **SC-003**: The Bias of the estimator is measured against the known true discontinuity effect embedded in the synthetic data generation process. (See FR-001, FR-007)
- **SC-004**: The computational runtime of the full Monte-Carlo simulation (1,000 replications per configuration) is measured against the 6-hour GitHub Actions runner limit to ensure feasibility. (See FR-006)

## Assumptions

- **Assumption about dataset-variable fit**: The synthetic data generation process is assumed to contain all necessary variables (running variable, outcome, covariates) required for the RD estimation and missingness mechanisms; no external real-world dataset gaps exist in the simulation.
- **Assumption about inference framing**: Since this is a simulation study with known ground truth, findings regarding bias and consistency are descriptive of the estimator's properties under the simulated conditions, not causal claims about real-world populations.
- **Assumption about threshold justification**: The bandwidth selection rule (Imbens-Kalyanaraman) is assumed to be the community standard for local-linear RD; the sensitivity analysis will sweep the bandwidth multiplier over {0.5, 1.0, 1.5} to verify robustness of the headline bias rates.
- **Assumption about compute feasibility**: The simulation of 1,000 replications for 3 mechanisms, 3 missing rates, and 4 estimators (approx. 36 configurations) is assumed to complete within the 6-hour GitHub Actions limit on 2 CPU cores, provided each replication is optimized to run in <0.2 seconds.
- **Assumption about measurement validity**: The `mice` package (or equivalent Python implementation) and logistic regression for IPW are assumed to be sufficiently validated statistical tools for the purpose of this comparative study.
- **Assumption about predictor collinearity**: In the synthetic data, the running variable and covariates are generated independently to avoid definitional collinearity that would confound the estimation of missing data impacts.