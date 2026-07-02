# Feature Specification: The Impact of Digital Decluttering on Cognitive Performance and Well-being

**Feature Branch**: `001-digital-decluttering-study`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does a one-week period of intentionally reduced digital engagement (digital decluttering) improve sustained attention, working memory capacity, and self-reported stress and mood compared to baseline levels?"

## User Scenarios & Testing

### User Story 1 - Baseline Data Collection (Priority: P1)

The system must recruit participants and collect their baseline cognitive and emotional metrics before any intervention begins. This establishes the control data necessary to measure change.

**Why this priority**: Without valid baseline measurements for SART (sustained attention), Ospan (working memory), PSS-10 (stress), and PANAS (mood), the study cannot calculate change scores or determine the intervention's effect. This is the foundational data layer.

**Independent Test**: Can be fully tested by running the recruitment and baseline script for a single participant and verifying that all four metric types are recorded in the dataset with valid ranges (e.g., SART commission errors > 0, PSS-10 scores between 0-40).

**Acceptance Scenarios**:

1. **Given** a recruited participant has not yet started the intervention, **When** they complete the baseline survey and cognitive tasks, **Then** their SART, Ospan, PSS-10, and PANAS scores are stored with a `baseline` timestamp.
2. **Given** a participant attempts to skip a cognitive task, **When** the system detects missing data, **Then** the participant is blocked from proceeding to the intervention phase until the data is provided or a valid reason is logged.

### User Story 2 - Intervention Compliance Logging (Priority: P2)

The system must allow participants to self-report their daily adherence to the digital decluttering rules (≤30 min social media, no news, notifications off) for seven consecutive days.

**Why this priority**: The validity of the "intervention" depends on actual behavior change. Without compliance logs, we cannot distinguish between "decluttering" and "no change," making the post-test results uninterpretable.

**Independent Test**: Can be fully tested by simulating a participant submitting 7 daily logs and verifying that the system calculates a compliance score (e.g., percentage of days meeting criteria) and flags any deviations.

**Acceptance Scenarios**:

1. **Given** a participant has completed Day 1 of the intervention, **When** they submit their daily log confirming ≤30 min social media use, **Then** the system records the entry as "compliant" and allows access to Day 2.
2. **Given** a participant reports exceeding the 30-minute limit on Day 3, **When** the log is submitted, **Then** the system marks that day as "non-compliant" but continues the study timeline (does not disqualify the participant).

### User Story 3 - Post-Intervention Analysis & Reporting (Priority: P3)

The system must compute change scores (post-pre) for all metrics, perform paired statistical tests (t-test or Wilcoxon), calculate effect sizes (Cohen's d), and generate visualizations of the results.

**Why this priority**: This delivers the final scientific output. It transforms raw data into the answer to the research question, enabling the conclusion about digital decluttering's impact.

**Independent Test**: Can be fully tested by feeding the system a synthetic dataset with known pre/post differences and verifying that the output report correctly identifies the statistical significance, effect size, and generates the expected plots.

**Acceptance Scenarios**:

1. **Given** a complete dataset with baseline and post-intervention scores, **When** the analysis script is executed, **Then** it outputs a summary table showing mean change, 95% confidence intervals, and p-values for all four metrics.
2. **Given** the data violates normality assumptions (Shapiro-Wilk p < 0.05), **When** the analysis runs, **Then** it automatically switches to Wilcoxon signed-rank tests instead of paired t-tests and reports the correct statistic.

### Edge Cases

- What happens when a participant drops out after Day 3? (System must handle missing post-intervention data gracefully, excluding them from the final analysis but retaining baseline data for descriptive stats).
- How does the system handle participants who fail the SART attention check (e.g., < 50% correct)? (System must flag these as low-quality data points and optionally exclude them from the primary analysis).
- What if a participant reports 0 minutes of digital use for all 7 days? (System must log this as an extreme case but include it in the analysis to avoid selection bias).

## Requirements

### Functional Requirements

- **FR-001**: System MUST recruit participants and assign them a unique ID to link baseline and post-intervention data while maintaining anonymity (See US-1).
- **FR-002**: System MUST administer the SART and Ospan cognitive tasks via a web interface and record response times and accuracy (See US-1).
- **FR-003**: System MUST administer the PSS-10 and PANAS questionnaires and record raw scores (See US-1).
- **FR-004**: System MUST provide a daily logging interface for participants to report social media time, news consumption, and notification status for 7 days (See US-2).
- **FR-005**: System MUST calculate change scores (post-intervention value minus baseline value) for all dependent variables (See US-3).
- **FR-006**: System MUST perform a normality check (Shapiro-Wilk) on the change scores and select the appropriate statistical test (paired t-test or Wilcoxon signed-rank) accordingly (See US-3).
- **FR-007**: System MUST calculate Cohen's d effect sizes with 95% confidence intervals for each outcome measure (See US-3).
- **FR-008**: System MUST apply a Bonferroni correction to the p-values to account for multiple hypothesis testing across the four outcome variables (See US-3).

### Key Entities

- **Participant**: Represents a study subject with a unique ID, demographic data, and two sets of measurement records (baseline, post).
- **MeasurementRecord**: Represents a single data point containing the metric type (SART, Ospan, PSS, PANAS), the value, the timestamp, and the phase (baseline/post).
- **ComplianceLog**: Represents a daily entry containing the date, reported social media minutes, boolean flags for news/notifications, and a derived compliance status.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The change in SART commission errors is measured against the baseline commission errors to determine improvement in sustained attention (See US-1, US-3).
- **SC-002**: The change in Ospan span scores is measured against the baseline span scores to determine improvement in working memory capacity (See US-1, US-3).
- **SC-003**: The change in PSS-10 total scores is measured against the baseline total scores to determine reduction in perceived stress (See US-1, US-3).
- **SC-004**: The change in PANAS positive/negative affect scores is measured against the baseline scores to determine improvement in mood (See US-1, US-3).
- **SC-005**: The statistical significance of the observed changes is measured against a family-wise error rate of α = 0.05, adjusted for four comparisons (See US-3).

## Assumptions

- **Assumption about data source**: The study assumes that the Open Science Framework (OSF) provides valid, web-accessible versions of the SART and Ospan tasks that function correctly in a standard browser without requiring local installation.
- **Assumption about sample size**: The study assumes a sample size of –60 participants is sufficient to detect a medium effect size (Cohen's d ≈ 0.5) with [deferred] power, acknowledging that a formal power analysis was not conducted in this design phase.
- **Assumption about compliance**: The study assumes that self-reported digital usage logs are sufficiently accurate for the purpose of a pilot study, despite the lack of objective screen-time tracking.
- **Assumption about compute**: The analysis assumes that the entire dataset (a moderate number of participants × 4 metrics) will fit comfortably within the 7 GB RAM limit of the GitHub Actions free-tier runner, allowing for standard Python/scipy operations.
- **Assumption about normality**: The study assumes that if the change scores violate normality, the Wilcoxon signed-rank test provides a robust non-parametric alternative without requiring large sample sizes.
- **Assumption about attrition**: The study assumes that the dropout rate will be ≤15%, allowing for a final analyzable sample of at least 34 participants, which is the minimum required for the planned power.
