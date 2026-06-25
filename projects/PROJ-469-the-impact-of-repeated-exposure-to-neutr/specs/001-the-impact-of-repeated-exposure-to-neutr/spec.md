# Feature Specification: The Impact of Self‑Reported Political News Exposure on Implicit Political Bias

**Feature Branch**: `001-political-news-implicit-bias`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Research question validation: Phenomenon-vs-method check pass. Topic: Impact of Self‑Reported Political News Exposure on Implicit Political Bias."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Associational Analysis (Priority: P1)

The research team MUST be able to load the Project Implicit dataset, verify the presence of required variables (IAT score, ideology, news exposure), and fit a linear regression model to estimate the associational relationship between news exposure frequency and implicit bias, including an interaction term for ideology.

**Why this priority**: This constitutes the primary scientific question. Without establishing the baseline associational model, no further robustness or reporting is possible.

**Independent Test**: Can be fully tested by executing the data loading and regression pipeline on a subset of the data and verifying the output coefficients and p-values.

**Acceptance Scenarios**:

1. **Given** the Project Implicit CSV and codebook are available, **When** the system loads the data, **Then** it must confirm the existence of columns for IAT D-score, ideology, and news exposure frequency.
2. **Given** valid data rows exist, **When** the regression model is fitted, **Then** it must output the interaction coefficient and its 95% confidence interval without crashing.

---

### User Story 2 - Robustness & Sensitivity Checks (Priority: P2)

The research team MUST be able to validate the stability of the interaction effect through bootstrap resampling and assess the sensitivity of the findings to the statistical significance threshold (alpha).

**Why this priority**: Observational data requires robustness checks to ensure findings are not artifacts of specific sampling or arbitrary p-value cutoffs.

**Independent Test**: Can be tested by running the bootstrap procedure and sensitivity sweep independently of the main reporting pipeline, verifying that confidence intervals remain stable across resamples.

**Acceptance Scenarios**:

1. **Given** the fitted model, **When** 1000 bootstrap resamples are generated, **Then** the 95% CI of the interaction effect must be calculable and finite.
2. **Given** the primary p-value threshold of 0.05, **When** the analysis is repeated at alpha levels {0.01, 0.10}, **Then** the system must report whether the significance status of the interaction term changes.

---

### User Story 3 - Reporting & Artifact Generation (Priority: P3)

The research team MUST be able to generate a consolidated PDF report and CSV summary tables containing model summaries, effect sizes, and plots, suitable for review.

**Why this priority**: Results must be preserved in a human-readable format for the methodology panel and downstream research stages.

**Independent Test**: Can be tested by inspecting the `results/` directory for the presence of the PDF report and CSV tables after pipeline completion.

**Acceptance Scenarios**:

1. **Given** the analysis completes successfully, **When** the reporting script runs, **Then** a PDF file ≤ 5 MB must be created in the `results/` directory.
2. **Given** the analysis completes successfully, **When** the reporting script runs, **Then** a CSV file containing model coefficients must be created in the `results/` directory.

---

### Edge Cases

- What happens when the downloaded dataset is missing the specific `news_exposure_freq` column name referenced in the codebook?
- How does the system handle rows with missing values for `IAT_D_score` or `political_ideology`?
- How does the system behave if the bootstrap resampling exceeds the 6-hour compute limit?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST validate the presence of `IAT_D_score`, `political_ideology`, and `news_exposure_freq` columns in the dataset before processing, raising a `[NEEDS CLARIFICATION]` error if any are missing (See US-1).
- **FR-002**: System MUST fit a linear regression model framing findings as ASSOCIATIONAL (not causal) with the formula `IAT_D ~ news_exposure_z * ideology_binary` (See US-1).
- **FR-003**: System MUST execute a non-parametric bootstrap with exactly 1000 resamples to estimate the stability of the interaction coefficient (See US-2).
- **FR-004**: System MUST perform a sensitivity analysis sweeping the significance threshold alpha over the set {0.01, 0.05, 0.10} and report the variation in significance status for the interaction term (See US-2).
- **FR-005**: System MUST export model summaries, effect-size tables, and plots to the `results/` directory in PDF and CSV formats within 6 hours of job start (See US-3).

### Key Entities *(include if feature involves data)*

- **Dataset**: Public Project Implicit "Political IAT" data (CSV), containing participant responses, IAT scores, and demographic variables.
- **Model**: Linear regression object storing coefficients, standard errors, and p-values for the interaction term.
- **Report**: PDF document aggregating statistical findings and visualizations for the methodology panel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* is measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data load success rate is measured against the requirement that ≥ 95% of valid rows are retained after filtering missing values (See US-1).
- **SC-002**: Model convergence rate is measured against the requirement that ≥ 99% of bootstrap resamples converge to a finite solution (See US-2).
- **SC-003**: Threshold sensitivity coverage is measured against the requirement that significance status is reported for all 3 alpha values {0.01, 0.05, 0.10} (See US-2).
- **SC-004**: Artifact completeness is measured against the requirement that both a PDF report and a CSV summary file exist in `results/` upon job completion (See US-3).

## Assumptions

- **Dataset Availability**: It is assumed the Project Implicit "Political IAT" dataset contains the required variables (`IAT_D_score`, `political_ideology`, `news_exposure_freq`); if variable names differ, the codebook mapping will be used (See FR-001).
- **Inference Framing**: It is assumed the study is observational; therefore, all findings must be framed as ASSOCIATIONAL, not causal, to avoid methodological invalidity.
- **Compute Constraints**: The analysis MUST run on a CPU-only environment (2 cores, ~7 GB RAM, ≤ 6 h); no GPU, CUDA, or large-model training is permitted.
- **Significance Standard**: The default alpha threshold is set to 0.05 based on community standards for psychological research, with sensitivity analysis required for robustness.
- **Measurement Validity**: It is assumed the IAT D-score and news exposure Likert scale are valid measures as per the Project Implicit codebook.
- **Power Limitation**: Sample size and power calculations are deferred to the research phase; the design acknowledges potential power limitations inherent in observational sub-group analysis.
