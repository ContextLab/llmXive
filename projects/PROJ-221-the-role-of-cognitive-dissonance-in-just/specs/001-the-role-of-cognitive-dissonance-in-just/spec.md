# Feature Specification: The Role of Cognitive Dissonance in Justifying Unethical AI Use

**Feature Branch**: `001-role-of-cognitive-dissonance`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Research on whether individuals who utilize AI tools for ethically ambiguous tasks exhibit higher moral disengagement scores than non-users, even when controlling for cognitive dissonance derived from a separate set of non-AI-specific ethical attitudes and behaviors."

## User Scenarios & Testing

### User Story 1 - Primary Regression Analysis Execution (Priority: P1)

The system MUST ingest a cleaned survey dataset, construct the predictor (AI usage frequency), outcome (moral disengagement score), and control (General Trait Empathy) variables, and execute a hierarchical multiple regression to test the independence of AI usage on moral disengagement.

**Why this priority**: This is the core scientific inquiry. Without this analysis, the research question remains unaddressed. It delivers the primary evidence required to validate or refute the hypothesis.

**Independent Test**: Can be fully tested by running the regression script on a synthetic dataset with known coefficients and verifying that the output reports the correct partial regression coefficient for the AI usage variable and the correct R-squared change.

**Acceptance Scenarios**:

1. **Given** a CSV file containing survey responses with valid columns for AI usage, ethical behavior, and disengagement scores, **When** the analysis script is executed, **Then** the script outputs a regression summary table containing the coefficient, standard error, t-statistic, and p-value for the AI usage variable in the second model step.
2. **Given** a dataset where the AI usage variable has zero correlation with the outcome after controlling for empathy, **When** the script runs, **Then** the output reports a p-value > 0.05 for the AI usage coefficient in the second step, indicating non-significance.

---

### User Story 2 - Bootstrapping Validation (Priority: P2)

The system MUST perform a sufficient number of bootstrap iterations on the regression model to generate confidence intervals for the AI usage coefficient, ensuring the result is robust to sampling variability and outliers.

**Why this priority**: Standard parametric assumptions may not hold for survey data. Bootstrapping provides a non-parametric validation of the primary finding, increasing the reliability of the conclusions.

**Independent Test**: Can be tested by running the bootstrapping routine on a small, fixed dataset and verifying that the generated confidence intervals (2.5th and 97.5th percentiles) are stable across multiple runs and do not include zero if the primary result is significant.

**Acceptance Scenarios**:

1. **Given** a primary regression result with a significant p-value, **When** the bootstrapping module runs 1,000 iterations, **Then** the output includes a 95% confidence interval for the AI usage coefficient that excludes zero.
2. **Given** a dataset with potential outliers, **When** the bootstrapping module runs, **Then** the resulting confidence intervals are reported alongside the parametric intervals to allow for comparison of stability.

---

### User Story 3 - Data Preprocessing and Variable Construction (Priority: P3)

The system MUST load raw survey data, retain all respondents (including those with zero AI usage), and compute the control variable using a validated General Trait Empathy scale (e.g., Interpersonal Reactivity Index) rather than a simple difference score.

**Why this priority**: This is the foundational step required for US-001 and US-002. Using a validated control variable (Empathy) instead of a derived difference score prevents circularity and ensures the control is theoretically distinct from the outcome (Moral Disengagement). Retaining all respondents ensures the necessary control group (non-users) is available for comparison.

**Independent Test**: Can be tested by providing a raw CSV with known values for "AI usage frequency" and "Empathy scale items" and verifying that the generated "empathy_score" column matches the validated scale calculation exactly.

**Acceptance Scenarios**:

1. **Given** a raw CSV where a respondent rates empathy items as [5, 4, 5, 4, 5] (sum=23), **When** the preprocessing script runs, **Then** the resulting "empathy_score" value is exactly 23.0.
2. **Given** a raw CSV containing respondents who never used AI (frequency=0), **When** the script runs, **Then** these respondents are retained in the dataset to serve as the control group for the regression analysis.

---

### Edge Cases

- **What happens when the dataset lacks the specific variable for "frequency of AI use"?** The system must log a `[NEEDS CLARIFICATION]` warning and halt, as the predictor cannot be constructed.
- **How does the system handle missing data in the "empathy" scale items?** The system must exclude rows with missing values in critical empathy items from the calculation of the control variable to prevent bias, and report the count of excluded rows.
- **What if the bootstrap iterations fail to converge or exceed the 6-hour runtime limit?** The system MUST return the partial results from the completed iterations (e.g., 500/1000) with a `convergence_status` flag set to `partial` and report the actual iteration count, overriding the target of [deferred] iterations defined in FR-004.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST load the survey dataset from a CSV source and retain all records, including those where the AI usage frequency is zero, serving the "Data Preprocessing" user story (See US-003).
- **FR-002**: The system MUST calculate the control variable as the sum of items from a validated General Trait Empathy scale (e.g., Interpersonal Reactivity Index), serving the "Variable Construction" user story (See US-003).
- **FR-003**: The system MUST perform a hierarchical multiple regression where Step 1 includes only the General Trait Empathy control and Step 2 adds the AI usage frequency variable, serving the "Primary Regression Analysis" user story (See US-001).
- **FR-004**: The system MUST attempt 1,000 bootstrap iterations on the final regression model to generate 95% confidence intervals for the AI usage coefficient, serving the "Bootstrapping Validation" user story (See US-002). If the process is interrupted or times out, it must return partial results as defined in the Edge Cases.
- **FR-005**: The system MUST report the change in R-squared ($\Delta R^2$) and the associated F-change statistic between Step 1 and Step 2 of the regression, serving the "Primary Regression Analysis" user story (See US-001).
- **FR-006**: The system MUST include the exact string "Associational Analysis Only" in the header of the output summary to explicitly frame results as non-causal, ensuring methodological correctness for observational data (See US-001).
- **FR-007**: The system MUST include a sensitivity analysis that sweeps the definition of "high-frequency AI usage" by applying binary thresholds to the continuous "AI usage frequency" variable at counts {1, 2, 3}, re-running the regression for each threshold to report the variation in the AI usage coefficient, serving the "Threshold Justification" requirement (See US-001).

### Key Entities

- **SurveyResponse**: Represents a single participant's data, containing attributes for AI usage frequency, empathy scale items, and moral disengagement score.
- **EmpathyScore**: A derived numeric value representing the magnitude of General Trait Empathy, calculated as the sum of validated scale items (e.g., IRI).
- **RegressionModel**: Represents the statistical model output, containing coefficients, p-values, R-squared values, and confidence intervals for the hierarchical steps.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of the partial regression coefficient for AI usage is measured against the null hypothesis (coefficient = 0) to determine statistical significance (See US-001).
- **SC-002**: The stability of the AI usage coefficient is measured against the distribution of coefficients generated from 1,000 bootstrap iterations (See US-002).
- **SC-003**: The change in model fit ($\Delta R^2$) is measured against the baseline model (empathy only) to quantify the unique variance explained by AI usage (See US-001).
- **SC-004**: The sensitivity of the results is measured against the variation in the AI usage coefficient across different frequency thresholds {1, 2, 3} used to define "high-frequency" groups (See US-001).
- **SC-005**: The validity of the control variable is measured against the use of a validated scale (e.g., IRI) to ensure it is distinct from the outcome construct (See US-003).

## Assumptions

- The public survey dataset (e.g., from Pew Research Center or OpenICPSR) contains at least one item measuring "frequency of AI use for ambiguous tasks" and one validated scale for "moral disengagement."
- The dataset contains a validated General Trait Empathy scale (e.g., Interpersonal Reactivity Index) that is not specific to AI, allowing for the construction of a control variable distinct from the outcome.
- The sample size of the available public dataset is sufficient to achieve statistical power (≥ 0.80) for detecting a medium effect size in a multiple regression with two predictors, or the analysis will explicitly report the power limitation.
- The "unethical use" variable can be reasonably operationalized as a binary or ordinal variable based on self-reported scenarios in the survey (e.g., agreement with statements about automated bias or misinformation).
- The analysis will be conducted using Python's `scikit-learn` and `scipy` libraries on a CPU-only environment, assuming no GPU acceleration is available.
- The dataset does not require complex weighting or imputation that would exceed the available memory resources of the GitHub Actions runner.
- **Justification for Sensitivity Analysis**: The sensitivity analysis sweeping frequency thresholds (FR-007) is retained as essential methodological rigor to validate the operationalization of the "high-frequency" predictor, addressing the requirement to ensure the relationship is robust to the definition of the independent variable.