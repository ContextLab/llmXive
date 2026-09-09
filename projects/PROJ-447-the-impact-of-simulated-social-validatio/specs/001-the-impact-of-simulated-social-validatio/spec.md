# Feature Specification: The Impact of Simulated Social Validation on Self-Perception in Adolescents

**Feature Branch**: `001-simulated-social-validation`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "The Impact of Simulated Social Validation on Self-Perception in Adolescents"

## User Scenarios & Testing

### User Story 1 - Data Acquisition, Validation, and Synthetic Generation (Priority: P1)

The researcher needs to successfully load and verify the availability of a dataset containing both social media engagement metrics (likes/comments) and psychometric self-report scores (self-esteem/body image) for the same individuals. Because public datasets linking these specific variables longitudinally are exceptionally rare due to privacy constraints (COPPA/GDPR), the system MUST also support a synthetic data generation protocol with known ground truth to validate the pipeline. Without this data match (real or synthetic), the research question cannot be addressed.

**Why this priority**: This is the foundational step. If the data does not exist or cannot be merged, the entire project fails immediately. It validates the feasibility of the study design.

**Independent Test**: The pipeline can be tested by attempting to load the specified dataset (real or synthetic) and checking for the presence of required columns (engagement counts, Rosenberg Self-Esteem Scale scores, comment sentiment scores, and temporal ordering). It delivers a binary "go/no-go" decision on project feasibility.

**Acceptance Scenarios**:

1. **Given** a raw dataset file is provided, **When** the data loader script executes, **Then** it must confirm the presence of at least one engagement metric column (e.g., likes count), one comment sentiment score column, and one validated self-esteem scale column.
2. **Given** the dataset is loaded, **When** the validation check runs, **Then** it must report the number of rows where both engagement and self-report data are non-null (N ≥ 100 to ensure minimal statistical power) AND confirm that engagement timestamps precede self-report timestamps for each participant (longitudinal requirement).
3. **Given** the dataset lacks the required longitudinal match OR the public dataset is unavailable, **When** the validation check runs, **Then** it must either explicitly flag the data gap and halt execution OR automatically invoke the Synthetic Data Generator to create a dataset with known ground truth parameters for validation purposes.

---

### User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

The researcher needs to run a multiple linear regression model to quantify the relationship between simulated social validation (predictor) and self-perception changes (outcome), controlling for demographics AND critical confounders (offline relationships, intrinsic traits), while ensuring the analysis frames results as associational rather than causal.

**Why this priority**: This is the core analytical engine. It directly answers the research question by calculating the effect size and significance, provided the data exists and confounders are controlled.

**Independent Test**: The analysis can be tested by running the regression on a synthetic dataset with known coefficients and verifying that the model recovers the correct coefficients and p-values within a small tolerance.

**Acceptance Scenarios**:

1. **Given** a valid dataset with matched variables, **When** the regression model executes, **Then** it must output a coefficient estimate for the validation metric with a 95% confidence interval, controlling for age, gender, offline relationship count, and intrinsic trait scores.
2. **Given** the analysis is observational (no randomization), **When** the results are generated, **Then** the output report must explicitly label the findings as "associational" and avoid causal language (e.g., "causes", "leads to").
3. **Given** multiple predictor variables are included, **When** the model runs, **Then** it must output Variance Inflation Factor (VIF) scores for all predictor variables to detect multicollinearity.

---

### User Story 3 - Robustness, Sensitivity, and Visualization (Priority: P3)

The researcher needs to verify the stability of the results against potential outliers, non-linear relationships, arbitrary threshold choices, AND the inclusion/exclusion of critical confounding variables, and visualize the findings for interpretation.

**Why this priority**: This ensures the scientific rigor of the findings. It addresses the "multiplicity", "sensitivity", and "confounding" requirements of the methodology panel, ensuring the results are not artifacts of specific data quirks or omitted variable bias.

**Independent Test**: The robustness check can be tested by artificially introducing outliers, shifting a decision threshold, or toggling confounder inclusion and verifying that the system reports the sensitivity of the results (e.g., p-value changes) rather than crashing or ignoring the change.

**Acceptance Scenarios**:

1. **Given** the primary regression results, **When** the sensitivity analysis runs, **Then** it must re-run the model with at least three different outlier handling strategies (e.g., none, IQR removal, winsorization) AND with the critical confounders (offline relationships, intrinsic traits) included and excluded, reporting the variation in the primary coefficient for each strategy.
2. **Given** a continuous predictor, **When** the non-linearity check runs, **Then** it must fit a quadratic term and report whether the quadratic coefficient is statistically significant (measured against the pre-registered alpha level [deferred]).
3. **Given** the final model, **When** the visualization module executes, **Then** it must generate a scatter plot with the regression line and a residual diagnostic plot saved to the output directory.

### Edge Cases

- What happens when the dataset contains zero rows with matched engagement and self-report data? (System must halt with a "Data Gap" error).
- How does the system handle missing values in the demographic control variables (e.g., age or gender)? (System must use listwise deletion or imputation, but must log the count of dropped rows).
- What happens if the VIF score for a predictor exceeds the pre-registered threshold [deferred]? (System must flag the variable in the results but continue execution, noting the limitation).
- What happens if the synthetic data generator fails to converge on the target distribution? (System must report the specific failure mode and halt).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and validate the presence of both social engagement metrics (e.g., likes count), comment sentiment scores, and validated psychometric scales (e.g., Rosenberg Self-Esteem Scale) in the input dataset, OR generate a synthetic dataset with known ground truth if the public dataset is unavailable (See US-1).
- **FR-002**: System MUST execute a multiple linear regression model with self-perception scores as the outcome and engagement metrics as the primary predictor, controlling for age, gender, offline relationship count, and intrinsic trait scores (See US-2).
- **FR-003**: System MUST calculate and report Variance Inflation Factors (VIF) for all predictor variables to detect multicollinearity (See US-2).
- **FR-004**: System MUST perform a sensitivity analysis by re-running the model with at least three different outlier handling strategies AND with critical confounders included/excluded, reporting the coefficient variation; if the variation exceeds the pre-registered stability threshold [deferred], the system MUST flag instability and halt (See US-3).
- **FR-005**: System MUST generate a scatter plot with the regression line and a residual diagnostic plot, saving them as PNG files (See US-3).
- **FR-006**: System MUST explicitly label all statistical findings as "associational" in the final output report, and MUST scan the output text for a predefined list of causal trigger words (e.g., 'causes', 'leads to', 'determines') and flag or reject the report if any are found (See US-2).
- **FR-007**: System MUST perform a non-linearity check by fitting a quadratic term for the primary predictor and reporting its significance (See US-3).
- **FR-008**: System MUST implement a measurement model that derives 'Perceived Social Validation' from the combination of engagement metrics and comment sentiment, rather than using raw engagement counts as a direct proxy for the psychological construct (See US-1).

### Key Entities

- **Participant**: Represents an individual adolescent in the dataset, containing attributes for age, gender, unique ID, offline relationship count, and intrinsic trait scores.
- **EngagementMetric**: Represents the social validation data, containing attributes for likes count, comment sentiment score, and timestamp.
- **PsychometricScore**: Represents the self-report data, containing attributes for Rosenberg Self-Esteem Scale score, Body Image Scale score, and perceived validation score (derived).
- **ModelResult**: Represents the output of the regression analysis, containing attributes for coefficients, p-values, confidence intervals, and VIF scores.
- **SyntheticDataConfig**: Represents the parameters for the synthetic data generator, including target correlation coefficients and distribution shapes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of rows with non-missing data for both engagement and self-report variables is measured against the minimum viable sample size of 100 (See US-1).
- **SC-002**: The Variance Inflation Factor (VIF) for every predictor is measured against the pre-registered multicollinearity threshold [deferred] to ensure no severe multicollinearity exists (See US-2).
- **SC-003**: The variation in the primary regression coefficient across the sensitivity analysis runs (outlier strategies and confounder inclusion) is measured against the pre-registered stability threshold [deferred] (See US-3).
- **SC-004**: The p-value of the quadratic term is measured against the pre-registered significance level [deferred] to determine if non-linear effects are present (See US-3).
- **SC-005**: The number of generated visualization files (scatter plot, residual plot) is measured against the requirement of a minimum set of files. (See US-3).

## Assumptions

- The project assumes that a public dataset containing both social media engagement logs and validated psychometric self-report scales (e.g., Rosenberg Self-Esteem Scale) for the same individuals is rare; therefore, the Synthetic Data Generator is a primary component of the validation strategy.
- The project assumes that the relationship between social validation and self-perception is linear enough for a multiple linear regression model to be a valid first-order approximation, subject to the non-linearity check.
- The project assumes that the "simulated" validation in the dataset (likes/comments) serves as a valid proxy for the psychological construct of "social validation" ONLY when processed through the measurement model defined in FR-008.
- The project assumes that the available dataset (or synthetic data) fits within the memory and disk constraints of the GitHub Actions free-tier runner without requiring complex sampling or chunking.
- The project assumes that the "longitudinal" aspect of the data is strictly required; cross-sectional data is insufficient to answer the research question and will cause the pipeline to fail or switch to synthetic generation.
- The project assumes that any missing data in demographic variables (age/gender) can be handled via listwise deletion without significantly biasing the results (i.e., missingness is not systematic).
- The project assumes that the "offline relationship count" and "intrinsic trait scores" are available in the dataset or can be reasonably simulated as confounders for the synthetic data generation.