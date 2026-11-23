# Specification: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## 1. Introduction

This document outlines the requirements and design for a study investigating the effect of nostalgia induction on cognitive flexibility in adults aged 65 and older. Cognitive flexibility is measured using the Wisconsin Card Sorting Test (WCST) metrics: perseverative errors and categories completed.

## 2. Goals

- **Primary Goal**: Determine if nostalgia induction improves cognitive flexibility compared to a neutral control condition.
- **Secondary Goal**: Assess the robustness of findings across different significance thresholds and cognitive impairment exclusions.

## 3. User Stories

### US1: Data Collection and Pre‑processing (See SC-001, SC-006)
As a researcher, I want to **collect** WCST data from participants aged 65+ under either a nostalgia‑induction or neutral control condition, validate that participants meet the age criterion, and exclude those with significant cognitive impairment (MMSE < 24) so that the dataset is clean, empirically grounded, and relevant to the target population.

### US2: Statistical Analysis and Hypothesis Testing (See SC-002, SC-003, SC-004, SC-007)
As a researcher, I want to perform statistical comparisons between the nostalgia and control groups using **Welch's independent samples t-test** to account for potential unequal variances, calculate Hedges' g with 95 % confidence intervals, apply Bonferroni correction for multiple outcomes, and monitor runtime, so that the results are statistically rigorous and reproducible.

### US3: Sensitivity Analysis and Robustness Check (See SC-005)
As a researcher, I want to perform sensitivity analyses by varying significance thresholds and re‑running analyses with and without cognitive impairment exclusions to ensure the findings are robust and not artifacts of specific parameter choices.

## 4. Functional Requirements

### FR-001: Data Collection & Validation (See US1)
The system must **collect** WCST data from participants aged ≥ 65 years under a nostalgia or neutral control stimulus, and validate that:
1. Age ≥ 65 (records failing this are excluded).
2. If MMSE is available, MMSE ≥ 24 (records failing this are excluded).
All retained records must be logged in `exclusion_log.json` with reasons for any exclusions.

### FR-002: Statistical Test Selection (See US2)
The system must use **Welch's independent samples t-test** (between‑subjects design) to compare the nostalgia and control groups for:
1. Perseverative Errors
2. Categories Completed

### FR-003: Multiple Comparison Correction (See US2)
The system must apply **Bonferroni correction** to p‑values resulting from the two primary outcome comparisons.

### FR-004: Effect Size Calculation (See US2)
The system must calculate **Hedges' g** with 95 % confidence intervals for all primary comparisons, providing a variance‑unbiased effect‑size estimate compatible with Welch's t-test.

### FR-005: Sensitivity Analysis (See US3)
The system must flag results as "sensitive to threshold choice" if any (uncorrected) p‑value falls within the borderline range **0.04 – 0.06** during sensitivity runs.

### FR-006: MMSE Exclusion (See US1)
If MMSE scores are available, participants with MMSE < 24 must be excluded from the primary analysis (see FR-001).

### FR-007: Runtime Monitoring (See US2)
The system must log a warning if the analysis runtime exceeds **6 hours** but continue to completion. (See US2)

## 5. Success Criteria

### SC-001 (See US1)
- After validation, **≥ 95 %** of collected participants remain (i.e., age and MMSE exclusions do not remove more than 5 % of the sample).
- `exclusion_log.json` accurately records counts of exclusions by reason.

### SC-002 (See US2)
- Welch's t-test yields a **Bonferroni‑corrected p‑value ≤ 0.05** for at least one primary outcome.

### SC-003 (See US2)
- Bonferroni correction is applied correctly: α_corrected = 0.05 / 2 = 0.025 for each of the two outcomes.

### SC-004 (See US2)
- Reported **Hedges' g** 95 % CI does **not include zero** for any statistically significant outcome (p ≤ 0.05 after correction).

### SC-005 (See US3)
- Sensitivity analysis reports a flag “sensitive to threshold choice” whenever any tested significance threshold yields a p‑value in the range **0.04 – 0.06**.

### SC-006 (See US1)
- `exclusion_log.json` contains a count of participants excluded due to MMSE < 24, and this count matches the number of records removed during preprocessing.

### SC-007 (See US2)
- A warning entry appears in the runtime log if wall‑clock execution time > 6 hours; the warning format is standardized (e.g., “WARNING: Runtime exceeded 6 hours”).

## 6. Data Model

### Input Schema (Raw)
- `participant_id`: string
- `age`: integer
- `stimulus_type`: string (nostalgia | control)
- `perseverative_errors`: float
- `categories_completed`: float
- `MMSE`: float (optional)

### Output Schema (Processed)
- `statistical_report.json`: Contains p‑values, Bonferroni‑corrected p‑values, Hedges' g with 95 % CI, power, and minimum detectable effect size (MDES).
- `sensitivity_report.json`: Contains significance status across tested thresholds.
- `exclusion_log.json`: Contains counts of excluded records by reason (age, MMSE).

## 7. Design Decisions

### Between‑Subjects Design
The study employs a between‑subjects design where participants are assigned to either the nostalgia or control condition. Therefore, **Welch's t-test** is the appropriate statistical method, not a paired t-test. This decision is mandated by the study design documented in the project plan.

### MMSE Threshold
A threshold of **24** is used for MMSE to exclude participants with significant cognitive impairment, ensuring the sample represents aging adults with intact cognitive function.

### Data Feasibility Justification
Public WCST datasets lack a `stimulus_type` column; consequently, the study will **collect new data** under controlled nostalgia and neutral conditions. This empirical data collection satisfies the scientific requirement for independent measurement of the predictor (nostalgia) and outcome (WCST performance), addressing prior scope and soundness concerns.

## 8. Validation

- **Citation Validation**: All data sources must be validated against their original citations with a title overlap score >= 0.7.
- **Stimulus Integrity**: Stimulus files must be validated against checksums stored in metadata.

## 9. Appendix: Change Log

- **T040 Update**: Updated FR-004 and SC-004 to use Hedges' g (variance‑unbiased) compatible with Welch's test.
- Revised SC-002 to remove non‑observable clause and make it directly verifiable.
- Added explicit justification for effect‑size choice in Design Decisions.
- Clarified that data collection will be performed anew rather than relying on synthetic stimulus assignment.
- Ensured all FR/SC links to User Stories remain intact and consistent.
