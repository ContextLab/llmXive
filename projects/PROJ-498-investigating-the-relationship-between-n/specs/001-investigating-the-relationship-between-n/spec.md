# Feature Specification: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Feature Branch**: `001-neural-synchrony-switching-costs`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Neural Synchrony and Attention Switching Costs"

## User Scenarios & Testing

### User Story 1 - Preprocess EEG Data and Extract Behavioral Metrics (Priority: P1)

The research system must ingest raw EEG data from OpenNeuro dataset ds (or equivalent), apply standard preprocessing pipelines (bandpass filtering, ICA artifact removal), and extract trial-by-trial reaction times and accuracy for switch vs. stay conditions.

**Why this priority**: This is the foundational data layer. Without clean, epoch-aligned EEG data and corresponding behavioral labels, no synchrony analysis can occur. It is the Minimum Viable Product (MVP) for the data engineering pipeline.

**Independent Test**: The system can be tested by running the preprocessing script on a single subject's data and verifying that the output contains a CSV with columns for `subject_id`, `trial_id`, `condition` (switch/stay), `reaction_time`, and `accuracy`, alongside cleaned EEG epochs.

**Acceptance Scenarios**:

1. **Given** raw EEG data file from OpenNeuro ds004173, **When** the preprocessing pipeline is executed with standard parameters (1–45 Hz filter, ICA), **Then** the system outputs a cleaned dataset with epochs ranging from -1000ms to +2000ms relative to stimulus onset and a corresponding behavioral CSV.
2. **Given** a subject with missing trials or artifacts exceeding 20% of the total, **When** the pipeline processes the data, **Then** the system flags the subject as "insufficient data" and excludes them from subsequent analysis steps without crashing.

---

### User Story 2 - Compute Pre-Stimulus Instantaneous Phase Difference (Priority: P2)

The system must calculate the Instantaneous Phase Difference (or weighted Phase-Lag Index over a sliding window of 5 trials) between frontoparietal electrode pairs (F3/F4, FC3/FC4 vs. P3/P4, CP3/CP4) in the theta (4–7 Hz) and gamma (30–45 Hz) bands during the -500ms to 0ms pre-stimulus window for each individual trial.

**Why this priority**: This implements the core novel hypothesis of the project. It transforms the raw data into the specific predictor variable (trial-level synchrony) required to test the research question. Using Instantaneous Phase Difference allows for a valid per-trial metric, unlike PLV which requires an ensemble.

**Independent Test**: The system can be tested by computing the metric on a subset of trials and verifying that the output matrix contains valid phase difference values (bounded between -π and π) for the specified frequency bands and electrode pairs, distinct from the post-stimulus window.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG epochs and the defined frontoparietal electrode montage, **When** the synchrony calculation module runs on the -500ms to 0ms window, **Then** the system outputs a feature matrix where each row represents a trial and columns represent the Instantaneous Phase Difference for theta and gamma bands.
2. **Given** a specific electrode pair (e.g., F3-P3), **When** the calculation is performed, **Then** the system correctly isolates the frequency bands 4–7 Hz and 30–45 Hz using a time-frequency decomposition method (Morlet wavelets with ≥7 cycles) ensuring side-lobe attenuation > 20 dB to prevent spectral leakage.

---

### User Story 3 - Statistical Analysis and Correlation Testing (Priority: P3)

The system must perform statistical tests using a linear mixed-effects model (LMM) to determine if pre-stimulus instantaneous phase difference predicts attention switching costs (reaction time) on a trial-by-trial basis, applying multiple-comparison corrections. Simple Pearson/Spearman correlation on subject-level means is performed only as a secondary descriptive check.

**Why this priority**: This delivers the final scientific answer. It connects the predictor (trial-level synchrony) to the outcome (trial-level RT) and validates the hypothesis with appropriate statistical rigor (LMM) that accounts for within-subject correlations.

**Independent Test**: The system can be tested by running the analysis on the generated feature/behavioral datasets and verifying that the output includes a fixed effect estimate, p-value, and confidence interval for the relationship between synchrony and reaction time, derived from the LMM.

**Acceptance Scenarios**:

1. **Given** the synchrony feature matrix and the behavioral reaction times, **When** the LMM analysis is executed, **Then** the system reports a fixed effect estimate and p-value, and applies a Bonferroni or FDR correction for the multiple tests performed (across bands and electrode pairs).
2. **Given** the full dataset, **When** the permutation test (1000 iterations) is run on the LMM fixed effect, **Then** the system generates a null distribution and reports the empirical p-value based on the proportion of permuted coefficients exceeding the observed coefficient.

---

### Edge Cases

- What happens when the number of trials for a specific subject is too low (< 20 switch trials) to calculate a reliable mean switching cost? The system must exclude the subject and log a warning.
- How does the system handle non-Gaussian distributions of reaction times (common in RT data)? The system must default to a log-transformed reaction time as the response variable in the LMM, or use a robust regression estimator, rather than switching to a simple correlation.
- What happens if the OpenNeuro dataset structure changes or a specific file is missing? The system must fail gracefully with a clear error message indicating the missing file, rather than producing silent NaN values.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the OpenNeuro ds004173 dataset (or equivalent) into a local directory structure compatible with MNE-Python, ensuring all raw EEG files and task events are accessible. (See US-1)
- **FR-002**: System MUST implement a preprocessing pipeline that applies a 1–45 Hz bandpass filter and performs ICA-based artifact removal on the EEG data, retaining epochs from -1000ms to +2000ms relative to stimulus onset. (See US-1)
- **FR-003**: System MUST compute Instantaneous Phase Difference (or weighted Phase-Lag Index over a sliding window of 5 trials) between defined frontoparietal electrode pairs (F3/F4/FC3/FC4 vs. P3/P4/CP3/CP4) specifically in the -500ms to 0ms pre-stimulus window for theta (4–7 Hz) and gamma (30–45 Hz) bands. The time-frequency decomposition MUST use Morlet wavelets with ≥7 cycles to ensure side-lobe attenuation > 20 dB. (See US-2)
- **FR-004**: System MUST fit a linear mixed-effects model (LMM) with trial-level data where the response variable is the reaction time (log-transformed if non-Gaussian) and the fixed effect is the pre-stimulus synchrony metric, with a random intercept for subject. The system MUST also calculate the mean switching cost per subject as a descriptive statistic only. (See US-3)
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to all statistical tests performed across frequency bands and electrode pairs to control the family-wise error rate at α ≤ 0.05. (See US-3)
- **FR-006**: System MUST execute the entire analysis pipeline (download to statistical output) on a CPU-only environment with ≤ 7 GB RAM and ≤ 6 hours total runtime, processing subjects sequentially if necessary. (See US-1, US-2, US-3)

### Key Entities

- **EEG_Epoch**: Represents a continuous segment of EEG data aligned to a stimulus event, containing time-series data for all channels and metadata (condition, trial_id, subject_id).
- **Synchrony_Feature**: Represents the calculated Instantaneous Phase Difference value for a specific electrode pair, frequency band, and time window, linked to a specific trial.
- **Behavioral_Trial**: Represents a single trial's behavioral outcome, containing reaction time, accuracy, and condition type (switch/stay).
- **Statistical_Result**: Represents the output of the hypothesis test, containing fixed effect estimates, p-values, confidence intervals, and correction flags.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system passes if it reports a statistically significant fixed effect (p < 0.05) with the predicted direction (negative correlation for synchrony vs. cost) OR explicitly reports a null result if p ≥ 0.05, based on a permutation test (1000 iterations) of the LMM. (See US-3)
- **SC-002**: The system passes if the multiple-comparison correction method is applied and the corrected p-value is reported. The result is considered significant if the corrected p-value < 0.05. (See US-3)
- **SC-003**: The computational feasibility is measured against the constraint of ≤ 6 hours total runtime and ≤ 7 GB RAM usage, verified by monitoring system resources during the sequential processing of all available subjects in the dataset. (See US-1, US-2, US-3)
- **SC-004**: The validity of the synchrony metric is measured against the requirement that the calculation window (-500ms to 0ms) strictly excludes post-stimulus activity, verified by checking the time-frequency decomposition boundaries. (See US-2)
- **SC-005**: The robustness of the behavioral metric is measured against the requirement that subjects with < 20 valid switch trials are excluded, ensuring the mean switching cost is calculated on a statistically sufficient sample size. (See US-1)

## Assumptions

- The OpenNeuro dataset ds004173 (or the selected equivalent) contains sufficient trial counts for both switch and stay conditions to calculate a reliable switching cost for at least 15 subjects.
- The standard 10-20 electrode montage (F3, F4, FC3, FC4, P3, P4, CP3, CP4) provides a valid proxy for the dorsolateral prefrontal and parietal cortical regions without requiring individual MRI source localization.
- The pre-stimulus window (-500ms to 0ms) is free of significant stimulus-evoked potentials that could confound the phase-locking value calculation, or that any residual evoked activity is negligible compared to the spontaneous synchrony of interest.
- The computational resources of the GitHub Actions free-tier runner (a limited number of CPU cores and approximately 7 GB RAM) are sufficient to process the selected EEG dataset sequentially without memory overflow., provided the analysis is not parallelized across subjects.
- The theta (4–7 Hz) and gamma (30–45 Hz) bands are the primary frequency bands of interest for frontoparietal communication in this specific task-switching paradigm, based on prior literature, and other bands (alpha, beta) are secondary or out of scope for the primary hypothesis.
- The reaction time data is approximately normally distributed or can be sufficiently normalized (e.g., via log transformation) to satisfy the assumptions of the linear mixed-effects model; if not, a robust regression estimator will be used within the LMM framework.