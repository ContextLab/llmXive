# Feature Specification: The Influence of Perceived Agency in AI Interactions on Trust

**Feature Branch**: `001-perceived-agency-trust`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does increasing a user's perception of agency in their interactions with an AI assistant—even when illusory—increase trust in the AI's recommendations?"

## User Scenarios & Testing

### User Story 1 - Experimental Task Execution and Data Capture (Priority: P1)

The system must present a simulated decision-making task to participants where they interact with an AI assistant under a specific agency condition (High, Low, or Control) and record their behavioral adherence and self-reported trust scores.

**Why this priority**: This is the core data generation mechanism. Without a functioning, randomized experimental interface that captures both behavioral (adherence) and psychometric (trust scale) data, no analysis can occur.

**Independent Test**: A test runner can simulate a participant session, verify that the randomization logic assigns the correct condition, confirm that the "illusory" controls in the High Agency condition do not alter the AI's output, and validate that the survey export contains the required columns (Condition ID, Adherence Rate, Trust Score).

**Acceptance Scenarios**:

1. **Given** a participant is assigned to the "High Perceived Agency" condition, **When** they interact with the interface using adjustable sliders, **Then** the sliders must be functional for user engagement but must NOT alter the underlying AI recommendation logic.
2. **Given** a participant completes the task, **When** the session ends, **Then** the system must record the percentage of AI recommendations followed and the raw scores from the Trust in Automation Scale (Lee & See, 2004).
3. **Given** a participant is in the "Control" condition, **When** they make a decision, **Then** the system must present a static, non-interactive display of an AI recommendation and record the decision, ensuring the presence of the agent is constant across all conditions and only the degree of control varies.

---

### User Story 2 - Statistical Analysis Pipeline Execution (Priority: P2)

The system must execute a reproducible statistical analysis pipeline on the collected survey data to determine if there are significant differences in trust and adherence across the three experimental conditions, specifically testing the directional hypothesis.

**Why this priority**: This transforms raw data into scientific findings. It validates the hypothesis by performing the required planned contrasts and post-hoc tests.

**Independent Test**: A script can be run against a synthetic dataset (or the actual collected data) to verify that the planned directional contrasts are computed correctly, post-hoc tests are generated for all pairwise comparisons, and Cohen's d effect sizes are calculated.

**Acceptance Scenarios**:

1. **Given** a valid CSV export of participant data, **When** the analysis script runs, **Then** it must execute planned directional contrasts (High vs. Low, and (High+Low) vs. Control) and output summary tables containing t-statistics, p-values, and degrees of freedom.
2. **Given** a significant contrast result, **When** post-hoc tests are triggered, **Then** the system must output pairwise comparisons (High vs. Low, High vs. Control, Low vs. Control) with adjusted p-values (Tukey method).
3. **Given** the analysis completes, **When** the results are generated, **Then** the system must calculate and report Cohen's d for all significant pairwise differences to quantify effect size.

---

### User Story 3 - Methodological Robustness & Sensitivity Reporting (Priority: P3)

The system must generate a report that includes power analysis verification, multiple-comparison corrections, and a sensitivity analysis of any decision thresholds used in the data processing.

**Why this priority**: This ensures the study meets the methodological soundness requirements (power, multiplicity, threshold justification) necessary for publication and scientific validity.

**Independent Test**: A review of the generated report must confirm that the power analysis targets ≥ 0.80 power for a medium effect size, that p-values are adjusted for family-wise error, and that a sensitivity sweep for any data-cleaning thresholds is performed.

**Acceptance Scenarios**:

1. **Given** the design parameters, **When** the power analysis module runs, **Then** it must confirm that the design targets ≥ 0.80 power to detect a medium effect size (f = 0.25) at α = 0.05, and generate a pre-study power calculation report documenting the required sample size.
2. **Given** multiple hypothesis tests are performed (3 pairwise comparisons), **When** the results are compiled, **Then** the system must apply a correction method (e.g., Tukey or Bonferroni) to control the family-wise error rate.
3. **Given** a data-cleaning threshold is applied (e.g., removing participants with < 80% attention check pass), **When** the sensitivity analysis runs, **Then** it must re-run the primary analysis with thresholds swept across a user-configurable range and report the variation in the primary outcome (trust difference).

---

### Edge Cases

- **What happens when** a participant fails the attention check or provides straight-lining responses? **System handles** this by flagging the record for exclusion based on the pre-registered threshold, but the sensitivity analysis (US-3) must verify if the main result holds even if these participants are retained.
- **How does system handle** a scenario where the planned contrast is non-significant (p > 0.05)? **System handles** this by clearly reporting the null result and the observed effect sizes, ensuring the finding is not misinterpreted as a failure of the tool but as a scientific outcome.
- **What happens when** the dataset size is smaller than the power analysis target? **System handles** this by calculating the achieved power post-hoc and explicitly stating the limitation in the final report, rather than forcing a significance claim.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST present three distinct experimental conditions (High Agency, Low Agency, Control) with randomized assignment to ensure independent variable manipulation (See US-1).
- **FR-002**: The system MUST capture behavioral adherence as a percentage (0-100%) and self-reported trust using the validated Lee & See (2004) scale items (See US-1).
- **FR-003**: The system MUST perform planned directional contrasts (High vs. Low, and (High+Low) vs. Control) to test the specific hypotheses regarding agency and AI presence (See US-2).
- **FR-004**: The system MUST compute and report Cohen's d effect sizes for all pairwise comparisons to quantify the magnitude of observed effects (See US-2).
- **FR-005**: The system MUST apply a multiple-comparison correction (e.g., Tukey HSD) to all pairwise p-values to control for family-wise error rate (See US-3).
- **FR-006**: The system MUST execute a sensitivity analysis sweeping the participant exclusion threshold across a user-configurable range (e.g., 0.75 to 0.90) and report the stability of the primary findings (See US-3).

### Key Entities

- **Participant**: Represents a unique user session, containing attributes for Condition ID, Adherence Rate, Trust Score, and Attention Check Status.
- **Experimental Condition**: Represents the manipulated variable (High Agency, Low Agency, Control), defining the interface constraints for the session.
- **Analysis Result**: Represents the output of the statistical pipeline, containing contrast statistics, pairwise comparisons, effect sizes, and power metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The primary outcome (difference in Trust Scores between High and Low Agency) is measured against the null hypothesis of no difference using planned directional contrasts (α = 0.05) (See US-2).
- **SC-002**: A pre-study power calculation report is generated confirming ≥ 0.80 power for a medium effect size (f = 0.25) at α = 0.05, determining the required sample size (See US-3).
- **SC-003**: The robustness of the primary finding is measured against the variation in p-values and effect sizes observed when the exclusion threshold is swept across a user-configurable range (See US-3).
- **SC-004**: The system MUST capture trust data using the exact item set and Likert scale structure defined in Lee & See (2004), verifiable by comparing the survey export schema against the source instrument (See US-1).
- **SC-005**: The control of Type I error is measured by the application of a family-wise error correction method (e.g., Tukey) across the pairwise comparisons (See US-3).

## Assumptions

- The participant recruitment via Prolific/MTurk will yield a sample size sufficient to achieve ≥ 0.80 power for a medium effect size, assuming a standard response rate for paid survey tasks.
- The "illusory" agency controls (sliders) are perceived by users as functional, even though they do not alter the AI's output, based on prior literature regarding the "illusion of control."
- The statistical analysis (planned contrasts, Tukey tests, power calculations) can be executed entirely on CPU within the GitHub Actions free-tier limit, as it relies on standard R/Python libraries (e.g., `pwr`, `statsmodels`, `scipy`) without GPU acceleration.
- The study is observational in nature regarding the *outcome* (trust), as participants are not randomly assigned to *believe* they have control, but the *condition* is randomized; thus, findings will be framed as associational regarding the psychological mechanism, not causal regarding the AI's actual capability.
- The dataset variables (Trust Score, Adherence Rate, Condition) are fully contained within the survey export, and no external data linkage is required.
- The "High Agency" condition effectively manipulates perceived control without introducing confounding variables (e.g., increased cognitive load) that would invalidate the trust measure.
- The Control condition (static AI display) is perceived as a valid AI interaction, ensuring the only manipulated variable is the degree of user control.