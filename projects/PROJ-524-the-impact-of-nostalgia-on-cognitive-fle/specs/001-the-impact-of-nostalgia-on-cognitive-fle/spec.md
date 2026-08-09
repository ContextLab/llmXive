# Specification: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## 1. Introduction

This document outlines the requirements and design for a study investigating the effect of nostalgia induction on cognitive flexibility in adults aged 65 and older. Cognitive flexibility is measured using the Wisconsin Card Sorting Test (WCST) metrics: perseverative errors and categories completed.

## 2. Goals

- **Primary Goal**: Determine if nostalgia induction improves cognitive flexibility compared to a neutral control condition.
- **Secondary Goal**: Assess the robustness of findings across different significance thresholds and cognitive impairment exclusions.

## 3. User Stories

### US1: Data Ingestion and Pre-processing
As a researcher, I want to ingest WCST and executive function data from public repositories, validate that participants are aged 65+, and exclude those with significant cognitive impairment (MMSE < 24) so that the dataset is clean and relevant to the target population.

### US2: Statistical Analysis and Hypothesis Testing
As a researcher, I want to perform statistical comparisons between the nostalgia and control groups using **Welch's independent samples t-test** to account for potential unequal variances, calculate effect sizes, and apply multiple comparison corrections so that the results are statistically rigorous.

### US3: Sensitivity Analysis and Robustness Check
As a researcher, I want to perform sensitivity analyses by varying significance thresholds and re-running analyses with and without cognitive impairment exclusions to ensure the findings are robust and not artifacts of specific parameter choices.

## 4. Functional Requirements

### FR-001: Data Validation
The system must validate that all participants are aged 65 or older. Records with missing age or age < 65 must be excluded.

### FR-002: Statistical Test Selection
**CRITICAL UPDATE**: The system must use **Welch's independent samples t-test** (between-subjects design) to compare the nostalgia and control groups.
*Previous implementation note: Paired t-tests were considered but rejected due to the between-subjects nature of the experimental design.*
The test must be applied to:
1. Perseverative Errors
2. Categories Completed

### FR-003: Multiple Comparison Correction
The system must apply Bonferroni correction to p-values resulting from multiple outcome comparisons.

### FR-004: Effect Size Calculation
The system must calculate Cohen's d with 95% confidence intervals for all primary comparisons.

### FR-005: Sensitivity Analysis
The system must flag results as "sensitive to threshold choice" if p-values fall within a borderline range (0.04 - 0.06).

### FR-006: MMSE Exclusion
If MMSE scores are available, participants with MMSE < 24 must be excluded from the primary analysis.

### FR-007: Runtime Monitoring
The system must log a warning if the analysis runtime exceeds 6 hours but continue to completion.

## 5. Data Model

### Input Schema (Raw)
- `participant_id`: string
- `age`: integer
- `stimulus_type`: string (nostalgia | control)
- `perseverative_errors`: float
- `categories_completed`: float
- `MMSE`: float (optional)

### Output Schema (Processed)
- `statistical_report.json`: Contains p-values, corrected p-values, effect sizes, power, and MDES.
- `sensitivity_report.json`: Contains significance status across thresholds.
- `exclusion_log.json`: Contains counts of excluded records by reason.

## 6. Design Decisions

### Between-Subjects Design
The study employs a between-subjects design where participants are assigned to either the nostalgia or control condition. Therefore, **Welch's t-test** is the appropriate statistical method, not a paired t-test. This decision is mandated by the study design documented in the project plan.

### MMSE Threshold
A threshold of 24 is used for MMSE to exclude participants with significant cognitive impairment, ensuring the sample represents "aging adults" with intact cognitive function.

## 7. Validation

- **Citation Validation**: All data sources must be validated against their original citations with a title overlap score >= 0.7.
- **Stimulus Integrity**: Stimulus files must be validated against checksums stored in metadata.

## 8. Appendix: Change Log

- **T040 Update**: Updated FR-002 and US-2 to explicitly specify Welch's independent samples t-test, replacing previous references to paired t-tests, to align with the between-subjects experimental design.