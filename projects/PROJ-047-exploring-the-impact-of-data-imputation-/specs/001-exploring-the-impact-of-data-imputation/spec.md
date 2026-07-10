# Feature Specification: Exploring the Impact of Data Imputation Methods on Causal Inference

**Feature Branch**: `001-explore-imputation-impact`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "How do different data imputation methods affect causal effect estimates under MNAR (Missing Not At Random) missingness mechanisms?"

## User Scenarios & Testing

### User Story 1 - Simulate MNAR Data and Compute Ground Truth (Priority: P1)

As a researcher, I need a reproducible pipeline that generates synthetic datasets with a known ground-truth Average Treatment Effect (ATE) and explicitly parameterized MNAR missingness mechanisms, so that I can quantify the exact bias introduced by imputation methods against a verified truth.

**Why this priority**: This is the foundational step. Without a controlled environment where the true causal effect and the missingness mechanism parameters are known, no comparison or bias quantification is possible. It defines the "control" for the experiment.

**Independent Test**: Can be fully tested by running the data generation script with fixed random seeds and verifying that the calculated ATE from the complete data matches the injected ground-truth parameter within an acceptable tolerance., and that the missingness rate in the outcome variable correlates with the outcome values as specified by the MNAR parameter $\beta$.

**Acceptance Scenarios**:

1. **Given** a configuration with MNAR strength parameter $\beta=0.5$ and sample size $N=1000$, **When** the data generation script runs, **Then** the dataset must contain a missingness indicator $M$ where $P(M=1|Y)$ follows the logistic model defined by $\beta$, and the complete-data ATE must equal the injected $\tau_{true}$ such that `abs(calculated_ate - tau_true) / abs(tau_true) < 0.01`.
2. **Given** multiple seeds (e.g., 1 to 200), **When** the generation loop executes, **Then** the distribution of missingness rates across replications must remain stable (standard deviation < 2%) to ensure consistent experimental conditions.

---

### User Story 2 - Apply Standard Imputation and Estimate Causal Effects (Priority: P2)

As a researcher, I need the system to apply three standard imputation methods (Mean, KNN, MICE) to the generated incomplete datasets and subsequently estimate the ATE using IPW and PSM, so that I can observe how standard pipelines perform when assumptions are violated.

**Why this priority**: This executes the core experimental manipulation. It tests the "treatment" (imputation methods) on the data prepared in Story 1. Without this, there is no data to analyze for bias.

**Independent Test**: Can be fully tested by feeding a single generated incomplete dataset into the imputation and estimation module and verifying that the output contains three distinct ATE estimates (one per method) and that no runtime errors occur during the MICE convergence or KNN neighbor search within the 6-hour CI limit.

**Acceptance Scenarios**:

1. **Given** a dataset with [deferred] missingness in the outcome $Y$ generated under MNAR, **When** the imputation pipeline runs, **Then** the system must produce a complete dataset for Mean, KNN (k=5), and MICE (5 iterations), and each must yield a valid ATE estimate (not NaN or infinite).
2. **Given** the imputed datasets, **When** IPW and PSM estimators are applied, **Then** the system must output the estimated ATE $\hat{\tau}$ and the standard error for each combination of imputation method and estimator.

---

### User Story 3 - Quantify Bias and Perform Statistical Sensitivity Analysis (Priority: P3)

As a researcher, I need the system to calculate the absolute bias and RMSE for each method, perform a repeated-measures ANOVA to test for significant differences, and sweep the MNAR parameter $\beta$ to identify the breakdown point, so that I can determine the threshold at which standard methods fail.

**Why this priority**: This delivers the final scientific insight. It transforms raw estimates into the "answer" to the research question, providing the evidence required to validate or refute the hypothesis about MNAR failure modes.

**Independent Test**: Can be fully tested by running the analysis script on the results of multiple replications and verifying that the output includes a table of bias values, a p-value from the ANOVA test, and a sensitivity plot showing bias vs. $\beta$, with the p-value < 0.05 if the hypothesis of difference is true.

**Acceptance Scenarios**:

1. **Given** the bias values from 200 replications across three imputation methods, **When** the statistical test runs, **Then** the system must output the F-statistic and p-value from the Aligned Rank Transform (ART) ANOVA, and if p < 0.05, flag the methods as significantly different.
2. **Given** a range of MNAR strengths $\beta \in \{0.1, 0.5, 1.0, 2.0\}$, **When** the sensitivity analysis runs, **Then** the system must generate a plot showing the divergence of bias for each method, and output the specific $\beta$ value from the set of candidate magnitudes where the Mean imputation bias first exceeds 10% of the true ATE, or output "none" if the condition is not met in the tested range.

### Edge Cases

- What happens when the MNAR parameter $\beta$ is so high that >90% of the outcome data is missing? (System must handle extreme sparsity without crashing, potentially flagging the result as unreliable).
- How does the system handle MICE convergence failure? (The pipeline must catch the exception, log the failure, and either retry with adjusted parameters or exclude that replication from the ANOVA with a clear flag).
- What if the synthetic data generation results in zero variance in the treatment variable? (The system must detect this and regenerate the dataset to ensure valid causal estimation).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate synthetic structural causal models with a binary treatment, continuous outcome, and confounders, ensuring a known ground-truth ATE $\tau_{true}$ is recorded for every replication. (See US-1)
- **FR-002**: The system MUST inject missingness into the outcome and confounders using a logistic model $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$ where $\beta$ is a configurable parameter controlling MNAR strength. (See US-1)
- **FR-003**: The system MUST implement and execute three imputation strategies: Mean imputation, K-Nearest Neighbors (k=5), and Multiple Imputation by Chained Equations (MICE) assuming MAR. (See US-2)
- **FR-004**: The system MUST estimate the ATE for each imputed dataset using both Inverse Probability Weighting (IPW) and Propensity Score Matching (PSM) to isolate imputation effects from estimator variance. (See US-2)
- **FR-005**: The system MUST calculate the absolute bias $|\hat{\tau}_{imp} - \tau_{true}|$ and RMSE for every method and replication, storing these metrics as "Total Deviation" to explicitly acknowledge the composite nature of the error under MNAR. (See US-3)
- **FR-006**: The system MUST perform an Aligned Rank Transform (ART) ANOVA to test the null hypothesis that bias is equal across imputation methods, prioritizing this non-parametric approach over standard ANOVA to handle non-normality and heteroscedasticity. (See US-3)
- **FR-007**: The system MUST perform a sensitivity analysis by sweeping the MNAR parameter $\beta$ over a defined set (e.g., $\{, 0.5, 1.0, 2.0\}$) and report how the mean bias changes for each method. (See US-3)

### Key Entities

- **SyntheticDataset**: Represents a generated dataset with attributes: `treatment` (binary), `outcome` (continuous), `confounders` (vector), `missingness_indicator` (binary), `ground_truth_ate` (float).
- **ImputationResult**: Represents the output of an imputation step: `method` (string), `imputed_data` (dataset), `convergence_status` (boolean).
- **CausalEstimate**: Represents the final metric: `imputation_method` (string), `estimator` (string), `estimated_ate` (float), `standard_error` (float), `bias` (float), `rmse` (float).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The magnitude of "Total Deviation" in ATE estimates is measured against the known ground-truth ATE ($\tau_{true}$) for each replication to quantify the combined distortion caused by MNAR identification bias and imputation error. (See FR-005)
- **SC-002**: The statistical significance of differences between imputation methods is measured against a conventional p-value threshold from the Aligned Rank Transform (ART) ANOVA test.. (See FR-006)
- **SC-003**: The robustness threshold of each method is measured by identifying the specific MNAR strength parameter $\beta$ from the set $\{, 0.5, 1.0, 2.0\}$ at which the absolute bias exceeds 10% of the true ATE. (See FR-007)
- **SC-004**: The computational feasibility is measured against the constraint that the entire simulation of 200 replications (including generation, imputation, and estimation) must complete within 6 hours on a 2-core CPU runner. (See FR-001, FR-002)
- **SC-005**: The validity of the missingness mechanism generator is verified by fitting a logistic regression of $M$ on $Y$ and confirming that the recovered coefficient $\hat{\beta}$ matches the injected $\beta$ within 10% relative error ($|\hat{\beta} - \beta| / |\beta| < 0.10$). (See FR-002)

## Assumptions

- **Dataset-variable fit**: The synthetic data generation process is assumed to perfectly contain all necessary variables (treatment, outcome, confounders) and the ability to control the missingness mechanism explicitly, as no external real-world dataset with verified MNAR mechanisms is available for this simulation study.
- **Inference framing**: Since the data is synthetic and the ground truth is known, the analysis frames findings as a direct quantification of bias (estimation error) rather than causal claims about real-world phenomena; the "causal" aspect is strictly the recovery of the known $\tau_{true}$.
- **Multiplicity & power**: The study assumes a sufficient number of replications to provide adequate statistical power to detect differences in bias distributions via ART ANOVA; if the effect size is small, the power limitation is acknowledged as a constraint of the simulation budget.
- **Threshold justification & sensitivity**: The threshold for "catastrophic failure" is defined as a bias magnitude >10% of the true ATE, based on a conservative standard for acceptable estimation error in applied statistics; a sensitivity analysis sweeping $\beta$ is required to verify the stability of this failure point.
- **Measurement validity**: The "true" ATE is derived from the structural causal model parameters, which is the gold standard for simulation studies; no external questionnaire or instrument validation is required as the variables are mathematically defined.
- **Predictor collinearity**: The synthetic confounders are generated with controlled correlation structures to avoid perfect collinearity, which would invalidate the causal estimation; the system will check for Variance Inflation Factors (VIF) > 10 and regenerate data if detected.
- **Compute feasibility**: The analysis assumes that standard Python libraries (`scikit-learn`, `statsmodels`, `fancyimpute` or `sklearn.impute`) can execute the imputation and estimation steps within the 7GB RAM and 6-hour time limit for $N=1000$ and 200 replications.
- **MNAR mechanism**: The project assumes that the logistic missingness model $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$ is a sufficient and representative model for MNAR mechanisms in this context, as it is the standard parametric form used in missing data literature.
- **Bias Interpretation**: The study explicitly assumes that under MNAR, standard estimators (IPW/PSM) cannot fully correct for the missingness mechanism; therefore, the "bias" metric represents the total deviation from truth, which is the intended subject of investigation.