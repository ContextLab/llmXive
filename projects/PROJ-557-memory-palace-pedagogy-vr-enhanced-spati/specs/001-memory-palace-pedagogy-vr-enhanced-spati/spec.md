# Feature Specification: Memory Load‑Adaptive Text Presentation for Abstract Concept Retention

**Feature Branch**: `001-memory-load-adaptive-text`  
**Created**: 2026-05-24  
**Status**: Draft  
**Input**: User description: "How does adapting the linguistic complexity of instructional text to moment‑by‑moment cognitive load affect long‑term retention of abstract concepts?"

## User Scenarios & Testing

### User Story 1 - Cognitive Load Index Calculation and Thresholding (Priority: P1)

The system must process raw pupil diameter time series from the Pupil Labs Reading dataset to compute a valid Cognitive Load Index (CLI) for every 2-second window, enabling the identification of high-load moments.

**Why this priority**: Without a reliable, quantifiable metric for cognitive load, the adaptive mechanism cannot function. This is the foundational data transformation required to distinguish between "high" and "low" load states for the subsequent text adaptation logic.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a subset of the dataset and verifying that the resulting CLI time series matches expected statistical properties (e.g., mean, variance) and that the 0.5 SD threshold correctly segments the data into high/low windows.

**Acceptance Scenarios**:

1. **Given** raw pupil diameter data with blinks removed, low-pass filtered at 4 Hz, and baseline-corrected, **When** the system computes a moving-average z-score per 2-second window, **Then** the output CLI values are normalized relative to the participant's mean and standard deviation.
2. **Given** a computed CLI time series, **When** the system identifies windows where CLI > 0.5 SD above the participant mean, **Then** these windows are flagged as "high-load" for downstream adaptation.

---

### User Story 2 - Simulated Adaptive Text Rendering (Priority: P2)

The system must dynamically select and present either the original or a simplified version of a passage sentence based on the real-time CLI state, creating the "adaptive" condition for analysis.

**Why this priority**: This implements the core experimental manipulation. It creates the distinct conditions (adaptive vs. control) required to test the hypothesis that load-dependent text modification improves retention.

**Independent Test**: Can be fully tested by simulating the presentation sequence for a participant, logging which text version (original vs. simplified) was selected for each window, and verifying that simplified text appears exclusively during high-CLI windows and original text during low-CLI windows.

**Acceptance Scenarios**:

1. **Given** a high-CLI window (CLI > 0.5 SD) for a passage with a available simplified paraphrase, **When** the system renders the text, **Then** the simplified version is displayed.
2. **Given** a low-CLI window (CLI ≤ 0.5 SD), **When** the system renders the text, **Then** the original complex version is displayed.
3. **Given** a high-CLI window where no simplified paraphrase exists in the dataset, **When** the system renders the text, **Then** the original version is displayed (graceful degradation).

---

### User Story 3 - Statistical Interaction Analysis (Priority: P3)

The system must fit a linear mixed-effects model to compare delayed recall scores between the adaptive and control conditions, specifically testing for a significant interaction between adaptation status and passage type (abstract vs. concrete). This analysis is framed as an associational study of a simulated counterfactual.

**Why this priority**: This delivers the primary scientific answer to the research question. It quantifies whether the adaptation strategy specifically benefits the retention of abstract concepts more than concrete ones, acknowledging the limitations of secondary analysis.

**Independent Test**: Can be fully tested by running the statistical analysis pipeline on the simulated dataset, generating the model coefficients, confidence intervals, and p-values, and verifying that the output format matches the required reporting standards.

**Acceptance Scenarios**:

1. **Given** the dataset with simulated adaptation labels (derived per window) and delayed recall scores, **When** the linear mixed-effects model `Recall ~ Adaptation*PassageType + (1|Participant)` is fitted, **Then** the output includes the β coefficient and 95% CI for the interaction term.
2. **Given** the fitted model, **When** a likelihood-ratio test is performed, **Then** the p-value for the interaction term is reported to determine statistical significance (p < 0.05).
3. **Given** the derived adaptation labels, **When** a permutation test with 10,000 shuffles is performed, **Then** the resulting p-value is reported to validate the association strength against the null hypothesis of random label assignment.

---

### Edge Cases

- What happens when the dataset contains passages that lack a corresponding simplified paraphrase? (System defaults to original text; this reduces the "adaptive" signal but prevents crashes).
- How does the system handle participants with missing delayed recall scores? (These participants are excluded from the primary analysis but logged for transparency).
- How does the system handle extreme pupil diameter outliers that persist after 4 Hz filtering? (Windows with values > 3 SD from the participant's mean are flagged and excluded from the CLI calculation).

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute a Cognitive Load Index (CLI) as a moving-average z-score of baseline-corrected and luminance-normalized pupil dilation per 2-second window, filtering raw data at 4 Hz and removing blinks. (See US-1)
- **FR-002**: System MUST identify high-load windows where CLI exceeds 0.5 standard deviations above the participant's mean. (See US-1)
- **FR-003**: System MUST select and render simplified text paraphrases for high-load windows when available, defaulting to original text otherwise. (See US-2)
- **FR-004**: System MUST fit a linear mixed-effects model with the formula `Recall ~ Adaptation*PassageType + (1|Participant)` to test the primary hypothesis of association. (See US-3)
- **FR-005**: System MUST perform a permutation test with exactly 10,000 shuffles on adaptation labels to validate that observed associations exceed chance. (See US-3)
- **FR-006**: System MUST report the interaction term's β coefficient, 95% confidence interval, and likelihood-ratio test p-value. (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis sweeping the CLI threshold over {0.3, 0.5, 0.7} SD to assess robustness of the interaction effect. (See US-3)
- **FR-008**: System MUST report the potential confounding risk (e.g., text difficulty vs. cognitive load) and explicitly state the non-causal nature of the findings in the output report. (See US-3)
- **FR-009**: System MUST apply baseline correction (per trial) and luminance normalization to raw pupil data before CLI calculation to control for physiological confounds. (See US-1)

### Key Entities

- **Participant**: An individual subject from the Pupil Labs Reading dataset, identified by a unique ID, with associated pupil time series and recall scores.
- **Passage**: A text segment (abstract or concrete) presented to the participant, containing attributes for original text, simplified text (if available), and lexical complexity tags.
- **Window**: A 2-second temporal slice of the pupil data, containing the computed CLI value and the associated passage context.
- **AdaptationLabel**: A binary flag (Adaptive/Control) assigned to each Window based on the CLI state during that specific 2-second interval.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of the association (β coefficient) between Adaptation and PassageType is measured against a null distribution generated by the 10,000-permutation test. (See US-3)
- **SC-002**: The consistency of the association effect across different CLI thresholds (0.3, 0.5, 0.7 SD) is measured against the primary result at 0.5 SD to confirm robustness. (See US-3)
- **SC-003**: Post-hoc statistical power is calculated and reported as a value between 0 and 1, with a target threshold of ≥ 0.80 for the observed effect size. (See US-3)
- **SC-004**: The computational runtime of the full pipeline (preprocessing + simulation + analysis) must be ≤ 30 minutes. (See Assumptions)

## Assumptions

- **Dataset Completeness**: The Pupil Labs Reading dataset contains both the original and simplified versions for a sufficient subset of passages to enable the adaptive simulation; if a passage lacks a simplified version, the analysis treats it as "original" (graceful degradation).
- **Physiological Validity**: Pupil dilation is a valid and reliable proxy for cognitive load in this specific reading context, provided that baseline correction and luminance normalization are applied (FR-009).
- **Threshold Justification**: The 0.5 SD threshold for defining "high load" is based on community standards for z-score segmentation in psychophysiology; the sensitivity analysis (FR-007) will verify that results are not an artifact of this specific choice.
- **Computational Feasibility**: The dataset size (OpenNeuro) and the proposed linear mixed-effects modeling (using `statsmodels` on CPU) will fit within the 7 GB RAM and 14 GB disk constraints of the GitHub Actions free-tier runner.
- **Non-Causal Interpretation**: As this is a secondary analysis of an observational dataset (no random assignment of text adaptation in the original study), all findings will be framed as associational; the "simulated" adaptation does not constitute a randomized controlled trial, and the permutation test validates association strength, not causal effect.
- **Power Limitation**: The study may be underpowered to detect small interaction effects; the analysis will report confidence intervals and effect sizes rather than relying solely on p-values.