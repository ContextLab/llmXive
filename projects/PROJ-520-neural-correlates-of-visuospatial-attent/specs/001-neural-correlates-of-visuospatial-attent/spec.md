# Feature Specification: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

**Feature Branch**: `001-neural-attention-navigation`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Analyze alpha and beta band power dynamics in parietal and frontal EEG channels during active versus passive visuospatial attention shifts in virtual navigation environments using OpenNeuro datasets"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - EEG Data Pipeline and Preprocessing (Priority: P1)

Download and preprocess OpenNeuro EEG datasets (suitable for navigation tasks with landmark cues) for navigation tasks with landmark cues, including bandpass filtering, artifact removal, and epoch segmentation around attention shift events.

**Why this priority**: This is the foundational data preparation step; without clean, properly segmented EEG data, no downstream analysis can proceed. The entire research question depends on valid epoch extraction.

**Independent Test**: Can be fully tested by verifying that the pipeline outputs a preprocessed data file containing ≥100 epochs labeled by condition (active/passive) with valid time-frequency features, and that the preprocessing runs successfully within the allocated CI time budget.

**Acceptance Scenarios**:

1. **Given** access to OpenNeuro dataset ds0001171, **When** the preprocessing pipeline executes, **Then** output contains ≥100 epochs with condition labels and no more than 20% of epochs rejected for artifacts
2. **Given** raw EEG data with line noise, **When** bandpass filtering (1-40 Hz) and ICA artifact rejection execute, **Then** output data shows ≤5% residual line noise at 50/60 Hz

---

### User Story 2 - Time-Frequency Feature Extraction (Priority: P2)

Extract mean power values from alpha (8-12 Hz) band over parietal (P3, Pz, P4) electrodes and beta (13-30 Hz) band over frontal (F3, Fz, F4) electrodes using Morlet wavelet decomposition for each epoch.

**Why this priority**: This operationalizes the core research question by transforming raw EEG into the specific frequency-band features needed to test for attention-related signatures. Without this step, the hypothesis cannot be evaluated.

**Independent Test**: Can be fully tested by verifying that feature extraction produces a matrix with dimensions (epochs × features) where features include alpha power from parietal electrodes and beta power from frontal electrodes, and that values fall within physiologically plausible ranges.

**Acceptance Scenarios**:

1. **Given** preprocessed epochs from US-1, **When** Morlet wavelet time-frequency decomposition executes (8-30 Hz), **Then** output contains mean power values for alpha band over parietal electrodes and beta band over frontal electrodes
2. **Given** epochs with attention shift events, **When** feature extraction completes, **Then** at least 80% of epochs have valid (non-NaN) feature values for all target electrodes

---

### User Story 3 - Classification and Statistical Validation (Priority: P3)

Train LDA classifier to distinguish active shift epochs from passive navigation baselines, validate using 5-fold cross-validation, and perform permutation testing (≥1000 iterations) to establish statistical significance (α = 0.05).

**Why this priority**: This tests the expected result (distinguishable neural signatures) and provides the statistical rigor required for the research question. Lower priority because it depends on successful completion of US-1 and US-2.

**Independent Test**: Can be fully tested by running the classification pipeline and verifying that accuracy, precision, and recall metrics are reported alongside a permutation p-value < 0.05 or a clear statement of non-significance.

**Acceptance Scenarios**:

1. **Given** extracted features from US-2, **When** LDA classifier trains with 5-fold cross-validation, **Then** output reports accuracy, precision, and recall with standard deviation across folds
2. **Given** classifier performance metrics, **When** permutation testing (1000 iterations) executes, **Then** output reports p-value and whether the null hypothesis (no class separation) is rejected at α = 0.05

---

### Edge Cases

- What happens when the OpenNeuro dataset has fewer attention shift events than required (e.g., <50 active epochs)? → System MUST flag insufficient sample size and report power limitation
- How does system handle missing electrode data (e.g., Pz channel not recorded)? → System MUST skip the affected electrode and document in output metadata
- What happens when ICA artifact rejection removes >30% of epochs? → System MUST log the rejection rate and proceed only if ≥70% epochs remain, otherwise halt with warning
- How does system handle datasets where attention shift events are not explicitly marked? → System MUST fall back to landmark interaction timestamps and document this substitution in assumptions

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download an OpenNeuro dataset and verify dataset contains EEG recordings with navigation task conditions (See US-1)
- **FR-002**: System MUST apply bandpass filter (1-40 Hz) and remove line noise at 50/60 Hz before epoch extraction (See US-1)
- **FR-003**: System MUST apply ICA-based artifact rejection with automatic component classification and manual review capability via log file or visual inspection interface (See US-1)
- **FR-004**: System MUST segment data into 2-second epochs centered on attention shift events with ≥100 epochs per condition (See US-1)
- **FR-005**: System MUST compute Morlet wavelet time-frequency decomposition for 8-30 Hz range across all epochs (See US-2)
- **FR-006**: System MUST extract mean power values from alpha (8-12 Hz) band over parietal (P3, Pz, P4) electrodes and beta (13-30 Hz) band over frontal (F3, Fz, F4) electrodes (See US-2)
- **FR-007**: System MUST train LDA classifier with 5-fold cross-validation and report accuracy, precision, recall metrics (See US-3)
- **FR-008**: System MUST perform permutation testing with ≥1000 iterations to establish statistical significance at α = 0.05 (See US-3)
- **FR-009**: System MUST apply family-wise error correction (e.g., Bonferroni or FDR) when testing multiple electrode-band comparisons (distinct from permutation testing which validates classifier accuracy) (See US-3)
- **FR-010**: System MUST conduct sensitivity analysis sweeping classification threshold across a range of absolute differences and report false-positive/false-negative rate variation (essential for robustness against threshold selection bias) (See US-3)

### Key Entities

- **Epoch**: A 2-second EEG segment centered on an attention shift event, containing raw signal and condition label (active/passive)
- **Feature**: Mean power value for a specific frequency band (alpha/beta) at a specific electrode (P3/Pz/P4/F3/Fz/F4)
- **Classifier**: LDA model trained on extracted features to distinguish active from passive navigation epochs

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Alpha desynchronization magnitude (8-12 Hz parietal power change) is measured against baseline passive navigation epochs (See US-2)
- **SC-002**: Classification accuracy for distinguishing active vs. passive epochs is measured against Constitution Principle VII benchmark standards. (mandatory pass/fail) and chance level (See US-3)
- **SC-003**: Statistical significance (p-value from permutation testing) is measured against α = 0.05 threshold (See US-3)
- **SC-004**: Multiple comparison correction (family-wise error rate) is measured against uncorrected p-values to quantify inflation (See US-3)
- **SC-005**: Power/sample-size adequacy is measured against minimum epoch count requirement (≥100 per condition, per standard EEG/MEG power convention) with explicit acknowledgment if underpowered (See US-1)
- **SC-006**: Sensitivity analysis threshold sweep results are measured against baseline accuracy to quantify robustness across cutoff values (See US-3)

## Assumptions

- An OpenNeuro dataset contains EEG recordings with navigation task conditions; system MUST verify dataset content before proceeding and halt if required conditions are absent
- The datasets contain sufficient EEG channels (P3, Pz, P4, F3, Fz, F4) for the specified electrode analysis
- Navigation task conditions are explicitly labeled in the dataset metadata, enabling active vs. passive epoch separation
- The OpenNeuro datasets have ≥200 total epochs (≥100 per condition) after artifact rejection to meet power requirements
- MNE-Python is available on the CI runner with all dependencies (numpy, scipy, scikit-learn) within the allocated compute budget
- OpenNeuro datasets in BIDS format contain event.tsv files with trial markers; if explicit attention shift markers are absent, the system falls back to landmark interaction timestamps as documented in edge cases (See Edge Cases - dataset event handling)
- Participant demographics (age, sex, handedness) are recorded in participants.tsv per BIDS convention; generalization claims are limited to the demographic distribution observed in the dataset with explicit acknowledgment of sample representativeness constraints (See SC-005)
- Within-subject analysis is supported if ≥30 trials per condition per participant are available (standard EEG/MEG power convention); otherwise analysis falls back to between-subject comparisons with explicit documentation of the limitation (See Edge Cases - sample size handling)
- Attention shift events are operationally defined as participant responses or landmark interactions; if neither is available, the system MUST flag the limitation and document the substitution in assumptions (See Edge Cases - dataset event handling)