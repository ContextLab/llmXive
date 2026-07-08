# Feature Specification: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

**Feature Branch**: `001-network-centrality-motor-consolidation`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on the Consolidation of Motor Memories"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system must successfully download the specified public resting-state fMRI dataset (OpenNeuro or equivalent), apply memory-efficient preprocessing to fit within constrained RAM resources, and extract behavioral motor sequence task performance metrics for all available subjects.

**Why this priority**: Without a valid, cleaned dataset containing both neural (fMRI) and behavioral (motor task) data, no subsequent analysis, modeling, or hypothesis testing can occur. This is the foundational step.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing subject IDs, behavioral improvement scores, and pre-processed fMRI time-series matrices, with no missing values for the core variables in the RETAINED subject set.

**Acceptance Scenarios**:

1. **Given** the OpenNeuro dataset URL is valid and accessible, **When** the download and preprocessing script runs on a CPU-only runner with 7 GB RAM, **Then** the output dataset must contain behavioral improvement scores and parcellated fMRI time-series for ≥ 50 subjects AND ≥ 80% of the total subjects available in the source dataset.
2. **Given** the input data includes subjects with incomplete behavioral records, **When** the preprocessing step executes, **Then** those subjects are explicitly flagged and excluded from the final analysis dataset without causing the pipeline to crash.

---

### User Story 2 - Centrality Calculation and Association Modeling (Priority: P2)

The system must compute network centrality metrics (degree, betweenness, eigenvector) from the resting-state functional connectivity matrices, aggregate them into a global centrality score, and fit a linear regression model to test the association between this score and behavioral consolidation improvement, while controlling for age and sex. The system must also test for non-linear relationships.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question by generating the primary statistical evidence (regression coefficients) linking baseline network topology to motor memory outcomes, while ensuring robustness against model misspecification.

**Independent Test**: The analysis script can be executed to output a regression summary table and a scatter plot with a regression line, demonstrating a statistically testable relationship (or lack thereof) between global centrality and improvement, including a non-linearity check.

**Acceptance Scenarios**:

1. **Given** a valid connectivity matrix for a subject, **When** the centrality calculation module runs, **Then** it must output three distinct centrality scores (degree, betweenness, eigenvector) for each of the parcellated regions using NetworkX on CPU.
2. **Given** the full dataset of centrality scores, **When** the aggregation step runs, **Then** it must compute a single 'global centrality' score per subject (e.g., mean of top [deferred] hub nodes) to serve as the primary predictor.
3. **Given** the full dataset of global centrality scores and behavioral improvements, **When** the regression model is fitted, **Then** it must produce a coefficient table where the p-value for the primary centrality predictor is calculated using a standard t-test, and the model includes age and sex as covariates.
4. **Given** the fitted linear model, **When** the non-linearity check runs, **Then** it must fit a generalized additive model (GAM) or polynomial term and report the difference in AIC/BIC to validate the linear assumption.

---

### User Story 3 - Validation and Robustness Assessment (Priority: P3)

The system must perform a permutation test to establish a null distribution for the observed regression coefficients and conduct k-fold cross-validation to assess out-of-sample prediction accuracy, ensuring the findings are not due to chance or overfitting.

**Why this priority**: This step validates the scientific rigor of the results. It addresses the "multiplicity & power" and "inference framing" methodological requirements, ensuring the observed association is robust and not a statistical artifact.

**Independent Test**: The validation module can be run to produce a histogram of the null distribution from a sufficient number of permutations and a cross-validated R² score, confirming the statistical significance and generalizability of the primary model.

**Acceptance Scenarios**:

1. **Given** the fitted linear regression model, **When** the permutation test (1000 shuffles) is executed, **Then** the observed regression coefficient must be compared against the null distribution to calculate an empirical p-value, and the result must be stored in the reproducibility report.
2. **Given** the dataset is split into 5 folds, **When** the cross-validation loop completes, **Then** the mean R² and RMSE across folds must be calculated and reported, with the standard deviation of these metrics included to assess stability.

### Edge Cases

- What happens if the public dataset (e.g., OpenNeuro ds000030) is temporarily unavailable or lacks the required motor task behavioral data? The system must fail gracefully with a clear error message indicating the specific missing data source, rather than hanging or producing silent errors.
- How does the system handle subjects where the fMRI preprocessing fails due to motion artifacts exceeding the quality threshold? These subjects must be automatically excluded, and a log of excluded subjects with reasons must be generated.
- What if the calculated centrality metrics are highly collinear (e.g., degree and eigenvector centrality)? The system must detect variance inflation factors (VIF) > 5 and flag the model for potential multicollinearity issues in the report, rather than silently producing unstable coefficients.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess the specified public resting-state fMRI dataset (e.g., OpenNeuro ds000030) to fit within constrained RAM resources, using memory-efficient settings for fMRIPrep or equivalent, to support the analysis of ≥ 50 subjects AND ≥ 80% of available subjects. (See US-1)
- **FR-002**: System MUST compute degree, betweenness, and eigenvector centrality metrics for each subject's functional connectivity matrix derived from a standard atlas (e.g., AAL or Harvard-Oxford) using NetworkX on CPU. (See US-2)
- **FR-002.1**: System MUST aggregate the regional centrality metrics into a single 'global centrality' score per subject (e.g., mean of the top hub nodes) to serve as the primary predictor for the regression model, reducing the multiple comparisons burden. (See US-2)
- **FR-003**: System MUST fit a linear regression model predicting behavioral consolidation improvement from the 'global centrality' score, explicitly including age and sex as covariates. Additionally, the system MUST fit a Generalized Additive Model (GAM) or polynomial regression to test for non-linear relationships and report the AIC/BIC difference. (See US-2)
- **FR-004**: System MUST execute a permutation test with ≥ 1000 shuffles to generate a null distribution and calculate an empirical p-value for the primary regression coefficient (using the global centrality score) to address multiple comparison concerns. (See US-3)
- **FR-004.1**: If regional-level analysis is performed, System MUST apply Benjamini-Hochberg FDR correction (α ≤ 0.05) to the resulting p-values to control the false discovery rate across the multiple tests. (See US-3)
- **FR-005**: System MUST perform k-fold cross-validation to report out-of-sample prediction accuracy (R² and RMSE) and standard deviation, ensuring the model is not overfitting the training data. (See US-3)
- **FR-006**: System MUST generate a `reproducibility_report.json` (JSON format) documenting all data URLs, code versions, and specific thresholds. This report MUST include a nested `pipeline_metrics` object containing `wall_clock_time_seconds`, `peak_ram_gb`, and `cpu_cores` fields to satisfy SC-005. (See US-1, US-2, US-3)

### Key Entities

- **Subject**: Represents an individual participant with unique ID, demographic data (age, sex), and associated neuroimaging/behavioral data.
- **Connectivity Matrix**: A symmetric matrix representing functional connectivity strengths between a set of brain regions for a specific subject.
- **Centrality Metrics**: A set of three numerical values (degree, betweenness, eigenvector) derived from the connectivity matrix for specific regions of interest.
- **Global Centrality Score**: A single numerical value derived by aggregating regional centrality metrics (e.g., mean of top hubs) to reduce dimensionality.
- **Consolidation Improvement**: A calculated behavioral score representing the percentage change in motor sequence performance from pre- to post-consolidation sessions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of subjects successfully processed (with valid behavioral and fMRI data) is measured against the total number of subjects in the source dataset to ensure data completeness. (See US-1)
- **SC-002**: The empirical p-value from the permutation test is measured against the standard significance threshold to determine statistical significance of the centrality-improvement association. (See US-3)
- **SC-003**: The out-of-sample R² score from 5-fold cross-validation is measured against a baseline representing no predictive power to assess the model's generalizability. (See US-3)
- **SC-004**: The Variance Inflation Factor (VIF) for predictors in the regression model is measured against a standard threshold to detect and report multicollinearity issues. (See FR-003, Edge Cases)
- **SC-005**: The total computational time of the analysis pipeline is measured against the time limit of the GitHub Actions free-tier runner, with the value recorded in the `wall_clock_time_seconds` field of the `reproducibility_report.json` artifact. (See FR-006)

## Assumptions

- The public OpenNeuro dataset (ds000030 or equivalent) contains both resting-state fMRI scans and a motor sequence task with pre- and post-consolidation behavioral measurements for a sufficient number of subjects (≥ 50) to perform a meaningful regression analysis.
- The analysis will be performed on a CPU-only environment (GitHub Actions free tier) with no GPU acceleration, requiring all methods (fMRIPrep, NetworkX, regression) to be optimized for single-threaded or multi-threaded CPU execution within 7 GB RAM limits.
- The "sleep-dependent consolidation" period is defined by the experimental design of the source dataset (e.g., a substantial delay between pre- and post-testing), and no additional sleep monitoring data is required for the analysis.
- The relationship between network centrality and motor memory consolidation is primarily linear, but the model includes a non-linearity check (GAM) to validate this assumption.
- The standard parcellation atlas (AAL or Harvard-Oxford) with a moderate number of regions provides sufficient spatial resolution for the centrality analysis without introducing excessive noise or computational overhead.
- Any missing data points in the source dataset (e.g., motion artifacts, missing behavioral trials) will be handled by exclusion rather than imputation to avoid introducing bias.
- The 'global centrality' aggregation strategy (mean of top [deferred] hubs) is a valid proxy for overall network integration in this context, reducing the multiple comparisons problem to a single primary test.