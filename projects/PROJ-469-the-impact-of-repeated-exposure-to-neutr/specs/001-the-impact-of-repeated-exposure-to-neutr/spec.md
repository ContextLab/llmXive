# Feature Specification: The Impact of Self‑Reported Political News Exposure on Implicit Political Bias

**Feature Branch**: `001-political-news-implicit-bias`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Research question validation: Phenomenon-vs-method check pass. Topic: Impact of Self‑Reported Political News Exposure on Implicit Political Bias."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Associational Analysis (Priority: P1)

The research team MUST be able to load the Project Implicit dataset, verify the presence of required variables (IAT score, ideology, news exposure) via codebook mapping, handle missing data via imputation, and fit a linear regression model to estimate the associational relationship between news exposure frequency and implicit bias, using continuous ideology as the primary moderator.

**Why this priority**: This constitutes the primary scientific question. Without establishing the baseline associational model with valid variable mapping and missing data handling, no further robustness or reporting is possible.

**Independent Test**: Can be fully tested by executing the data loading, imputation, and regression pipeline on a subset of the data and verifying the output coefficients, p-values, and imputation diagnostics.

**Acceptance Scenarios**:

1. **Given** the Project Implicit CSV and codebook are available, **When** the system loads the data, **Then** it must confirm the existence of required variables by attempting to map them via the codebook; if mapping fails, it must raise a `ValueError` with a message listing the missing columns.
2. **Given** valid data rows exist, **When** the regression model is fitted, **Then** it must output the interaction coefficient (continuous ideology) and its 95% confidence interval without crashing.

---

### User Story 2 - Robustness & Sensitivity Checks (Priority: P2)

The research team MUST be able to validate the stability of the interaction effect through bootstrap resampling, assess sensitivity to the significance threshold (alpha), and verify robustness against model specification changes (covariates).

**Why this priority**: Observational data requires robustness checks to ensure findings are not artifacts of specific sampling, arbitrary p-value cutoffs, or omitted variable bias.

**Independent Test**: Can be tested by running the bootstrap procedure, alpha sweep, and covariate-added model independently of the main reporting pipeline, verifying that confidence intervals and significance status are reported correctly.

**Acceptance Scenarios**:

1. **Given** the fitted model, **When** 1000 bootstrap resamples are generated, **Then** the 95% CI of the interaction effect must be calculable and finite.
2. **Given** the primary p-value threshold of 0.05, **When** the analysis is repeated at alpha levels {0.01, 0.05, 0.10}, **Then** the system must report whether the significance status of the interaction term changes.
3. **Given** the primary model, **When** covariates (age, gender, education) are added, **Then** the system must report the change in the interaction coefficient magnitude and significance.

---

### User Story 3 - Reporting & Artifact Generation (Priority: P3)

The research team MUST be able to generate a consolidated PDF report and CSV summary tables containing model summaries, effect sizes, power analysis results, and plots, suitable for review.

**Why this priority**: Results must be preserved in a human-readable format for the methodology panel and downstream research stages.

**Independent Test**: Can be tested by inspecting the `results/` directory for the presence of the PDF report and CSV tables after pipeline completion.

**Acceptance Scenarios**:

1. **Given** the analysis completes successfully, **When** the reporting script runs, **Then** a PDF file ≤ 5 MB must be created in the `results/` directory.
2. **Given** the analysis completes successfully, **When** the reporting script runs, **Then** a CSV file containing model coefficients and imputation diagnostics must be created in the `results/` directory.

---

### Edge Cases

- **Missing Column Names**: If the dataset lacks the exact column names for `IAT_D_score`, `political_ideology`, or `news_exposure_freq`, the system attempts to map them using the provided codebook. If mapping fails, the system raises a `ValueError` with a message: "Required variables missing after codebook mapping: [list]".
- **Missing Values**: If rows contain missing values for key variables, the system applies Multiple Imputation by Chained Equations (MICE) with 5 imputations. If missingness exceeds 50% for a key variable, the system halts and logs a warning.
- **Compute Limits**: If bootstrap resampling exceeds the 6-hour compute limit, the system saves the current state and reports the partial convergence rate and confidence intervals calculated so far.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST validate the presence of `IAT_D_score`, `political_ideology`, and `news_exposure_freq` (or their codebook-mapped equivalents) in the dataset before processing. If mapping fails, the system MUST raise a `ValueError` with a message listing the missing columns (See US-1).
- **FR-002**: System MUST fit a primary linear regression model framing findings as ASSOCIATIONAL (not causal) with the formula `IAT_D ~ news_exposure_z * political_ideology` (continuous), including an interaction term (See US-1).
- **FR-003**: System MUST execute a non-parametric bootstrap with exactly 1000 resamples to estimate the stability of the interaction coefficient (See US-2).
- **FR-004**: System MUST perform a significance reporting analysis sweeping the alpha threshold over the set {0.01, 0.05, 0.10} and report the variation in significance status for the interaction term (See US-2).
- **FR-005**: System MUST export model summaries, effect-size tables, power analysis results, and plots to the `results/` directory in PDF and CSV formats within 6 hours of job start (See US-3).
- **FR-006**: System MUST define derived variables explicitly: `news_exposure_z` is the z-scored version of `news_exposure_freq` (mean=0, SD=1); `political_ideology` is used as a continuous ordinal variable for the primary model. A binary version (`ideology_binary`) using a median split is defined ONLY for secondary sensitivity checks (See US-2).
- **FR-007**: System MUST perform an a priori power analysis (using G*Power or equivalent) to estimate the minimum sample size required to detect the interaction effect with power ≥ 0.80 at α = 0.05, and report whether the actual sample size meets this target (See US-1).
- **FR-008**: System MUST handle missing data for key variables using Multiple Imputation by Chained Equations (MICE) with 5 imputations. If the missingness rate for any key variable exceeds 50%, the system MUST halt and log a warning (See US-1).
- **FR-009**: System MUST perform a model specification robustness check by re-fitting the model with added covariates (age, gender, education) and report the change in the interaction coefficient magnitude and significance compared to the primary model (See US-2).

### Key Entities *(include if feature involves data)*

- **Dataset**: Public Project Implicit "Political IAT" data (CSV), containing participant responses, IAT scores, and demographic variables.
- **Codebook**: Metadata file mapping raw column names to standardized variable names (`IAT_D_score`, `political_ideology`, `news_exposure_freq`).
- **Model**: Linear regression object storing coefficients, standard errors, and p-values for the interaction term (continuous ideology).
- **Report**: PDF document aggregating statistical findings, power analysis, and visualizations for the methodology panel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* is measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data load success rate is measured against the requirement that the system calculates and reports the retention rate (rows_after_imputation / rows_before_imputation) and the missingness rate per variable (See US-1).
- **SC-002**: Model convergence rate is measured against the requirement that the system calculates and reports the percentage of bootstrap resamples that converged to a finite solution (See US-2).
- **SC-003**: Threshold sensitivity coverage is measured against the requirement that significance status is reported for all 3 alpha values {0.01, 0.05, 0.10} (See US-2).
- **SC-004**: Artifact completeness is measured against the requirement that both a PDF report and a CSV summary file exist in `results/` upon job completion (See US-3).
- **SC-005**: Power adequacy is measured against the requirement that the system reports the achieved power for the interaction effect given the sample size and observed effect size (See US-1).

## Assumptions

- **Dataset Availability**: It is assumed the Project Implicit "Political IAT" dataset contains the required variables (`IAT_D_score`, `political_ideology`, `news_exposure_freq`) or that a codebook mapping exists to identify them; if mapping fails, the system raises a `ValueError` (See FR-001).
- **Inference Framing**: It is assumed the study is observational; therefore, all findings must be framed as ASSOCIATIONAL, not causal, to avoid methodological invalidity.
- **Compute Constraints**: The analysis MUST run on a CPU-only environment (2 cores, ~7 GB RAM, ≤ 6 h); no GPU, CUDA, or large-model training is permitted.
- **Significance Standard**: The default alpha threshold is set to 0.05 based on community standards for psychological research, with sensitivity analysis required for robustness.
- **Measurement Validity**: It is assumed the IAT D-score and news exposure Likert scale are valid measures as per the Project Implicit codebook.
- **Power Analysis**: A priori power analysis is required to validate the study design; the assumption that the sample size is sufficient is explicitly tested via FR-007 and SC-005.
- **Missing Data Mechanism**: It is assumed missingness is Missing At Random (MAR) or Missing Completely At Random (MCAR) for the purpose of MICE imputation; if Missing Not At Random (MNAR) is suspected, a sensitivity analysis is noted as future work.