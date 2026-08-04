# Specification: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview
This document defines the requirements, user stories, and data models for the study investigating how nostalgia induction affects cognitive flexibility in adults aged 65 and older.

## Critical Design Note
**Statistical Analysis Methodology Update**:
Per the project Plan (FR-002 revision), the primary statistical analysis for User Story 2 has been updated from a "paired t-test" to a **Welch's independent samples t-test**.
- **Reasoning**: The study design utilizes a between-subjects approach where participants are assigned to either a "Nostalgia" or "Control" condition, rather than a within-subjects repeated measures design.
- **Implication**: All hypothesis testing in `code/analysis.py` must use `scipy.stats.ttest_ind` with `equal_var=False` (Welch's t-test).
- **Effect Size**: Cohen's d must be calculated for independent samples, not paired samples.

## User Stories

### US-1: Data Ingestion and Pre-processing
**Goal**: Ingest publicly available WCST/Executive Function data and nostalgia stimuli, validate age ≥ 65, and produce a clean, aligned dataframe.
**Acceptance Criteria**:
- Raw data is fetched from real sources (OpenML/HuggingFace) or simulation mode is explicitly triggered.
- Data is filtered for `age >= 65`.
- Records with missing `stimulus_type`, `perseverative_errors`, or `categories_completed` are excluded.
- If `MMSE` column exists, records with `MMSE < 24` are excluded.
- A cleaned dataset `data/processed/cleaned_dataset.csv` is produced.
- An exclusion log `data/processed/exclusion_log.json` is generated.

### US-2: Statistical Analysis and Hypothesis Testing
**Goal**: Execute statistical comparison of cognitive flexibility metrics between nostalgia and control conditions using **Welch's independent samples t-test**.
**Acceptance Criteria**:
- **FR-002**: The system performs a **Welch's independent samples t-test** comparing `perseverative_errors` and `categories_completed` between the `nostalgia` and `control` groups.
- Multiple comparison correction (Bonferroni) is applied.
- Effect sizes (Cohen's d) with 95% CI are calculated.
- Statistical power and Minimum Detectable Effect Size (MDES) are reported.
- Results are saved to `data/results/statistical_report.json`.

### US-3: Sensitivity Analysis and Robustness Check
**Goal**: Perform sensitivity analysis by sweeping significance thresholds and checking robustness against cognitive impairment exclusions.
**Acceptance Criteria**:
- Sensitivity sweep is performed across thresholds (0.01, 0.05, 0.1).
- Robustness check re-runs analysis excluding participants with `MMSE < 24` (if data available).
- Borderline results (p-value 0.04-0.06) are flagged.
- Final sensitivity summary is generated.

## Data Model

### Raw Dataset Schema
- `participant_id`: string (unique identifier)
- `age`: integer (years)
- `stimulus_type`: string (categorical: "nostalgia", "control")
- `perseverative_errors`: integer (WCST metric)
- `categories_completed`: integer (WCST metric)
- `MMSE`: integer (optional, 0-30)

### Processed Output Schema
- `participant_id`: string
- `stimulus_type`: string
- `perseverative_errors`: float
- `categories_completed`: float
- `age`: int

## Functional Requirements

### FR-001: Data Source Validation
The system must validate that data sources contain a citation DOI or metadata indicating a validation study.

### FR-002: Statistical Test Implementation (UPDATED)
The system must implement **Welch's independent samples t-test** for between-subjects comparisons.
- **Input**: Two independent groups defined by `stimulus_type`.
- **Output**: t-statistic, degrees of freedom, p-value, and effect size.
- **Constraint**: Do not use paired t-tests. Use `equal_var=False`.

### FR-003: MMSE Filtering
If MMSE data is available, participants scoring below 24 must be excluded from the primary analysis to ensure cognitive health.

### FR-004: Exclusion Logging
All exclusion steps (age, missing data, MMSE) must be logged with counts in `exclusion_log.json`.

### FR-005: Sensitivity Reporting
The system must flag results that are sensitive to small changes in the significance threshold (borderline p-values).

### FR-006: Stimulus Integrity
Stimulus files must be validated against checksums provided in metadata.

### FR-007: Runtime Monitoring
If runtime exceeds 6 hours, a warning must be logged, but the process continues.

## Non-Functional Requirements

### SC-001: Data Validity
At least 90% of raw records must pass validation filters to proceed.

### SC-002: Reproducibility
All random seeds must be fixed where applicable.

### SC-003: Error Handling
The system must fail loudly if real data cannot be fetched and simulation mode is not explicitly enabled.

## Appendix: Statistical Methodology Details

### Welch's t-test Formula
$t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}}$
Where $s_1^2$ and $s_2^2$ are the sample variances, and $n_1, n_2$ are sample sizes.
Degrees of freedom are approximated using the Welch-Satterthwaite equation.

### Cohen's d (Independent Samples)
$d = \frac{\bar{X}_1 - \bar{X}_2}{s_{pooled}}$
Where $s_{pooled} = \sqrt{\frac{(n_1-1)s_1^2 + (n_2-1)s_2^2}{n_1 + n_2 - 2}}$