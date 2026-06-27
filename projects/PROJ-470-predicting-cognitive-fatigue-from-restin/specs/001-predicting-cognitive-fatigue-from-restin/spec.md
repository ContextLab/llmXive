# Feature Specification: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Feature Branch**: `001-cognitive-fatigue-eeg-complexity`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Cognitive Fatigue from Resting-State EEG Complexity"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Retrieval and Preprocessing (Priority: P1)

The researcher MUST be able to retrieve EEG data from PhysioNet and preprocess it to remove artifacts and line noise, preparing it for complexity analysis.

**Why this priority**: Without clean, accessible data, no analysis can occur. This is the foundational step for the entire pipeline.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single sample EEG file and verifying the output file contains filtered data without crashes.

**Acceptance Scenarios**:

1. **Given** a valid PhysioNet dataset ID, **When** the system downloads the data, **Then** the local file structure matches the expected format.
2. **Given** raw EEG data with line noise, **When** the system applies the bandpass filter, **Then** the output spectrum shows attenuation outside 1-40 Hz.

---

### User Story 2 - Complexity Feature Extraction (Priority: P2)

The researcher MUST be able to calculate Lempel-Ziv complexity and permutation entropy for resting-state segments extracted from the preprocessed data.

**Why this priority**: These metrics are the primary predictors defined in the research question; extraction must be accurate and reproducible.

**Independent Test**: Can be fully tested by running the complexity calculation on a synthetic signal with known properties and verifying the output values fall within expected ranges.

**Acceptance Scenarios**:

1. **Given** a resting-state segment ≥ 120 seconds, **When** the system calculates Lempel-Ziv complexity, **Then** a numeric value is returned for each channel.
2. **Given** a resting-state segment ≥ 120 seconds, **When** the system calculates permutation entropy, **Then** a numeric value is returned for each channel.

---

### User Story 3 - Correlation Analysis and Reporting (Priority: P3)

The researcher MUST be able to correlate the extracted complexity metrics with subjective fatigue scores, controlling for confounds, and generate a report with statistical significance.

**Why this priority**: This delivers the final scientific insight (the answer to the research question) and ensures methodological soundness (power, multiplicity, validity).

**Independent Test**: Can be fully tested by running the analysis script on a mock dataset with known correlation values and verifying the reported p-values and coefficients match the mock truth.

**Acceptance Scenarios**:

1. **Given** paired complexity and fatigue data, **When** the system runs the correlation analysis, **Then** it outputs Pearson/Spearman coefficients and p-values.
2. **Given** multiple electrode channels, **When** the system runs the analysis, **Then** it applies multiple-comparison correction to the p-values.

---

### Edge Cases

- **What happens when** a participant has missing fatigue ratings? The system MUST exclude that participant from the correlation analysis but log the exclusion count.
- **How does system handle** EEG artifacts exceeding the rejection threshold? The system MUST flag the segment and exclude it from complexity calculation, logging the rejection reason.
- **What happens when** the dataset lacks the required fatigue variable? The system MUST halt and report a `[NEEDS CLARIFICATION]` error regarding variable availability.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve data from PhysioNet containing resting-state EEG and subjective fatigue ratings [NEEDS CLARIFICATION: does the selected PhysioNet subset contain post-task subjective fatigue ratings?], excluding participants without both measures (See US-1).
- **FR-002**: System MUST preprocess EEG data using MNE-Python with a bandpass filter (1-40 Hz) and reject bad channels/epochs based on amplitude thresholds (See US-1).
- **FR-003**: System MUST calculate Lempel-Ziv complexity and permutation entropy for each channel on resting-state segments ≥ 120 seconds (See US-2).
- **FR-004**: System MUST perform Pearson or Spearman correlation between complexity changes and fatigue delta scores, framing findings as associational rather than causal (See US-3).
- **FR-005**: System MUST apply Benjamini-Hochberg correction for multiple comparisons across all tested electrodes to control family-wise error rate (See US-3).
- **FR-006**: System MUST execute sensitivity analysis on the significance threshold by sweeping p-values over {0.05, 0.01} and reporting variation in significant findings (See US-3).
- **FR-007**: System MUST execute on CPU-only infrastructure without CUDA/GPU dependencies, ensuring memory usage ≤ 7 GB and runtime ≤ 6 hours (See US-1).

### Key Entities

- **EEG Segment**: Represents a time-locked resting-state recording (e.g., 2-5 min) with metadata (participant ID, pre/post task status).
- **Complexity Metric**: Represents the calculated value (Lempel-Ziv or Permutation Entropy) for a specific channel and segment.
- **Fatigue Score**: Represents the subjective rating (e.g., Likert scale) collected via validated questionnaire.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Sample size N ≥ 30 participants is measured against the power requirement for [deferred] power at r=0.3 (See US-3).
- **SC-002**: Total pipeline runtime ≤ 6 hours is measured against the free-tier CI job limit (See US-1).
- **SC-003**: Memory usage ≤ 7 GB is measured against the free-tier CI runner constraint (See US-1).
- **SC-004**: Collinearity diagnostics (VIF < 5) are measured against the requirement for independent predictor validity if metrics are combined (See US-3).

## Assumptions

- PhysioNet API access is available without authentication for public datasets.
- MNE-Python library is pre-installed in the CI environment or installable within the time budget.
- Resting-state segments are at least 120 seconds long in the selected dataset.
- Subjective fatigue ratings are collected using a validated instrument (e.g., NASA-TLX or Borg Scale).
- The analysis assumes an observational design; no randomization of fatigue states occurs.
- Free-tier CI runners provide stable network access to download EEG data files.
- No GPU accelerators are available; all computations must rely on standard CPU arithmetic.
