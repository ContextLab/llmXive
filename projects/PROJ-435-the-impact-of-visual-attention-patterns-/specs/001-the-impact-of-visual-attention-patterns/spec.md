# Feature Specification: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

**Feature Branch**: `001-impact-of-visual-attention-patterns`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines"

## User Scenarios & Testing

### User Story 1 - Core Data Ingestion and Preprocessing (Priority: P1)

The system must ingest raw eye-tracking datasets, apply standard fixation detection algorithms (I-VT or I-DT), and filter out low-quality participant data to ensure a clean dataset for analysis.

**Why this priority**: Without a validated, cleaned dataset, no statistical analysis can be performed. This is the foundational step that enables all subsequent research questions to be answered.

**Independent Test**: The pipeline can be fully tested by running the preprocessing script on a provided sample dataset and verifying that the output contains only participants with <20% data loss and that fixation events are correctly timestamped and mapped to Regions of Interest (ROIs).

**Acceptance Scenarios**:

1. **Given** a raw eye-tracking dataset with known noise, **When** the preprocessing script runs with the I-VT algorithm, **Then** the output dataset excludes participants with >20% data loss and correctly identifies fixations with a minimum duration of 100ms.
2. **Given** a dataset with missing bounding box coordinates for ROIs, **When** the script attempts to map gaze points to ROIs, **Then** the system logs a warning for missing coordinates and excludes those specific trials from the analysis while retaining valid trials.

---

### User Story 2 - Mixed-Effects Regression Analysis (Priority: P2)

The system must execute a mixed-effects regression model to test the three-way interaction between visual attention (source fixation duration), headline emotional valence, and cognitive reflection scores on belief susceptibility. The outcome variable is defined as a post-hoc self-reported belief rating collected via a survey question after the eye-tracking task, ensuring independence from the gaze predictor.

**Why this priority**: This is the primary scientific mechanism to answer the research question. It directly addresses the gap in understanding how attention, emotion, and cognition interact.

**Independent Test**: The model can be tested independently by running the regression script on a synthetic dataset with known interaction coefficients and verifying that the estimated coefficients match the synthetic truth within a 5% margin of error, while correctly identifying the random intercepts for participants and headlines.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with source fixation duration, valence scores, and cognitive reflection scores, **When** the regression model is fitted, **Then** the output includes the three-way interaction term (fixation × valence × cognitive reflection) with a p-value and confidence interval.
2. **Given** a dataset where the interaction effect is null, **When** the model is fitted, **Then** the output correctly reports a non-significant p-value (p ≥ 0.05) for the interaction term, preventing false positive claims.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

The system must perform robustness checks including alternative fixation thresholds, controls for headline length, and sensitivity analysis on the fixation duration cutoff to ensure findings are not artifacts of arbitrary parameter choices.

**Why this priority**: Scientific validity requires that results are robust to methodological variations. This addresses the "threshold justification" requirement and ensures the findings are generalizable.

**Independent Test**: The robustness suite can be tested by running the analysis with modified parameters (e.g., 50ms vs 150ms thresholds) and verifying that the direction and significance of the main effect remain consistent across these variations.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the robustness script runs with alternative fixation thresholds (50ms, 150ms), **Then** the output reports the variation in the mean belief rating across these thresholds, confirming the stability of the main finding.
2. **Given** a significant interaction effect, **When** the sensitivity analysis sweeps the cutoff over {0.01, 0.05, 0.1}, **Then** the system generates a report showing how the false-positive rate varies, ensuring the conclusion holds across the tested range.

---

### Edge Cases

- What happens when the eye-tracking dataset has no valid source attribution ROIs for certain headlines? The system must exclude those trials and log the exclusion count.
- How does the system handle participants with zero fixations on the source ROI? The analysis must treat this as a valid data point (fixation duration = 0) rather than a missing value, as zero attention is a meaningful behavioral signal.
- How does the system handle extreme outliers in cognitive reflection scores? The system must cap outliers at the 1st and 99th percentiles to prevent skewing the regression coefficients.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw eye-tracking data and apply I-VT or I-DT fixation detection with a 100ms minimum duration threshold (See US-1).
- **FR-002**: System MUST filter participants with >20% data loss before analysis (See US-1).
- **FR-003**: System MUST calculate headline emotional valence using the NRC Emotion Lexicon applied to headline text; if coverage is < 50%, the system MUST automatically switch to the VADER lexicon and log the switch (See US-2).
- **FR-004**: System MUST execute a mixed-effects regression model with a self-reported Likert-scale belief rating (collected post-task) as the outcome and source fixation duration, valence, and cognitive reflection as fixed effects, plus participant and headline as random intercepts (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis sweeping the fixation duration cutoff over {50ms, 100ms, 150ms} and report the resulting variation in the mean belief rating (See US-3).
- **FR-006**: System MUST frame reported findings as causal regarding the effect of attention on belief, given the experimental design with controlled stimuli (See US-2).
- **FR-007**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) when testing more than one hypothesis to control family-wise error rate (See US-2).

### Key Entities

- **Participant**: Represents an individual in the study, identified by a unique ID, with attributes including cognitive reflection score and random intercept for the model.
- **Stimulus**: Represents a news headline, identified by a unique ID, with attributes including text content, calculated emotional valence, and random intercept for the model.
- **GazeEvent**: Represents a fixation event, with attributes including timestamp, duration, and mapped ROI (source attribution, headline body, etc.).
- **AnalysisResult**: Represents the output of the regression model, containing coefficients, p-values, confidence intervals, and interaction terms.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of participants with >20% data loss is measured against the exclusion threshold of 20% to ensure data quality (See US-1).
- **SC-002**: The regression output file MUST contain a p-value field for the three-way interaction term (See US-2).
- **SC-003**: The variation in the mean belief rating is measured across the swept fixation duration cutoffs {50ms, 100ms, 150ms} to assess robustness (See US-3).
- **SC-004**: The family-wise error rate is measured against the alpha level of 0.05 after applying multiple-comparison correction to ensure validity of multiple tests (See US-2).
- **SC-005**: The total runtime of the analysis pipeline is measured against a 300-minute wall-clock limit on the 'ubuntu-latest' GitHub Actions runner to ensure compute feasibility (See US-1, US-2, US-3).

## Assumptions

- The publicly available eye-tracking datasets (e.g., from University of Dundee or Boston University) contain the necessary variables: raw gaze coordinates, bounding box definitions for source attribution ROIs, and post-task belief ratings.
- The NRC Emotion Lexicon provides sufficient coverage for the emotional valence calculation of the specific headlines in the dataset; if not, a fallback lexicon (e.g., VADER) will be used as documented in the preprocessing script.
- The cognitive reflection scores are provided as a continuous variable in the dataset; if only categorical data is available, the analysis will be adapted to use ordinal regression or treat the score as a categorical moderator.
- The analysis will run on a CPU-only environment (GitHub Actions free tier) using Python libraries (pandas, statsmodels, scikit-learn) that are compatible with this constraint; no GPU acceleration will be required.
- The dataset size is sufficient to fit within ~7 GB RAM and ~14 GB disk; if the raw dataset exceeds this, a random sample of participants will be drawn to ensure feasibility without biasing the interaction effects.
- The study design is experimental with controlled stimuli; therefore, findings regarding the relationship between attention and belief support causal inference (internal validity), consistent with the methodological soundness requirements.
- The "WYSIATI" effect (System 1 confidence assignment) is captured by the combination of fixation duration and subsequent belief rating; the protocol assumes that the belief rating serves as a proxy for the confidence in the belief formed after attention.