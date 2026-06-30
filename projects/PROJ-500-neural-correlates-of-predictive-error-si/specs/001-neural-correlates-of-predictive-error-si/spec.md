# Feature Specification: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Feature Branch**: `001-neural-correlates-tactile-learning`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does the amplitude of somatosensory mismatch negativity (MMN) attenuate as behavioral accuracy improves during tactile texture discrimination learning?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download raw EEG datasets from OpenNeuro matching specific tactile/somatosensory criteria, preprocess them (filtering, ICA, interpolation), and epoch the data into standard/deviant trials with a success rate of ≥ 95% for datasets meeting the inclusion criteria (≥20 subjects, ≥500 trials).

**Why this priority**: Without clean, correctly epoched data, no analysis of MMN amplitude or behavioral alignment is possible. This is the foundational step for the entire research project.

**Independent Test**: Can be fully tested by executing the data ingestion script on a sample dataset and verifying the output contains correctly labeled epochs, filtered signals, and interpolated channels without manual intervention.

**Acceptance Scenarios**:

1. **Given** a dataset ID from OpenNeuro that meets the "tactile" and "odd-ball" search filters, **When** the ingestion script runs, **Then** the system downloads the raw data and converts it to MNE-Python format within 15 minutes.
2. **Given** raw EEG data with known bad channels, **When** the preprocessing step runs, **Then** the system applies a 1–40 Hz bandpass filter, removes artifacts via ICA (removing ≥ 1 identified component), and interpolates bad channels, resulting in a continuous cleaned signal.
3. **Given** a cleaned dataset, **When** the epoching step runs, **Then** the system extracts epochs from a pre-stimulus baseline period to a post-stimulus interval relative to stimulus onset, correctly separating standard and deviant stimuli based on metadata, with a trial count loss of ≤ 5% due to artifact rejection.

---

### User Story 2 - MMN Amplitude and Behavioral Alignment (Priority: P2)

The system MUST compute the somatosensory mismatch negativity (MMN) amplitude at specific electrodes (CP3, CP4, C3, C4) in the 150–250ms window and align these neural signals with behavioral accuracy calculated in 50-trial learning blocks.

**Why this priority**: This step generates the core variables (neural error signal and behavioral performance) required to test the primary hypothesis. It transforms raw data into analyzable metrics.

**Independent Test**: Can be fully tested by running the alignment module on a pre-processed dataset and verifying the output CSV contains a time-series of MMN amplitudes and corresponding accuracy percentages for each block, with no missing values for valid blocks.

**Acceptance Scenarios**:

1. **Given** epoch data with standard and deviant trials, **When** the MMN calculation runs, **Then** the system computes the difference wave (deviant minus standard) and extracts the mean amplitude in the 150–250ms window for electrodes CP3, CP4, C3, and C4.
2. **Given** behavioral response logs and trial epochs, **When** the alignment step runs, **Then** the system bins trials into 50-trial blocks, calculates the accuracy percentage per block, and merges this with the corresponding MMN amplitude for that block.
3. **Given** a subject with < 30 valid trials in a specific block, **When** the alignment step runs, **Then** the system flags that block as "insufficient data" and excludes it from the final analysis dataframe to prevent noise in the correlation.

---

### User Story 3 - Statistical Modeling and Validation (Priority: P3)

The system MUST fit a linear mixed-effects model (MMN ~ Accuracy + (1|Subject)) to test the correlation, apply a multiple-comparison correction if multiple hypotheses are tested, and run a permutation test (n=1000) to validate significance.

**Why this priority**: This provides the statistical evidence for the research question. It moves from descriptive data to inferential conclusions, addressing the core "Does X attenuate as Y improves?" question.

**Independent Test**: Can be fully tested by executing the analysis script on the aligned dataset and verifying the output includes the model coefficients, p-values (corrected), and a permutation test p-value, all generated within 6 hours on CPU-only hardware.

**Acceptance Scenarios**:

1. **Given** the aligned dataset with MMN amplitudes and accuracy per block, **When** the statistical model runs, **Then** the system fits a linear mixed-effects model with "Accuracy" as the fixed effect and "Subject" as the random intercept, outputting the slope coefficient and p-value.
2. **Given** a p-value < 0.05 from the initial model, **When** the validation step runs, **Then** the system performs a permutation test with a sufficient number of shuffles of the accuracy labels and reports the empirical p-value.
3. **Given** a result where the observed statistic falls within the top [deferred] of the null distribution, **When** the validation step completes, **Then** the system flags the result as "statistically significant (p < 0.05)" in the final report.

### Edge Cases

- What happens when an OpenNeuro dataset has missing metadata for stimulus types (standard vs. deviant)? The system MUST log a warning and skip that specific dataset, rather than crashing.
- How does the system handle a subject with zero behavioral accuracy in all blocks? The system MUST exclude that subject from the mixed-effects model to avoid singularity issues in the linear regression.
- How does the system handle datasets where the 150–250ms window contains no data (e.g., due to excessive artifact rejection)? The system MUST mark the MMN amplitude for that block as NaN and exclude it from the correlation analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse raw EEG data from OpenNeuro for datasets matching the "tactile", "somatosensory", and "odd-ball" filters with ≥20 subjects and ≥500 trials (See US-1).
- **FR-002**: System MUST apply a 1–40 Hz bandpass filter, perform ICA-based artifact removal, and interpolate bad channels using MNE-Python (See US-1).
- **FR-003**: System MUST epoch data from -200ms to 500ms relative to stimulus onset and separate standard/deviant trials based on protocol metadata (See US-1).
- **FR-004**: System MUST compute MMN amplitude as the mean difference wave (deviant minus standard) in the 150–250ms window at electrodes CP3, CP4, C3, and C4 (See US-2).
- **FR-005**: System MUST segment behavioral data into 50-trial bins and calculate accuracy per bin to align with neural epochs (See US-2).
- **FR-006**: System MUST fit a linear mixed-effects model (MMN ~ Accuracy + (1|Subject)) to test the correlation between neural error and behavioral performance (See US-3).
- **FR-007**: System MUST perform a permutation test (n=1000) to validate the significance of the correlation against a null distribution (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) if the analysis involves testing multiple electrode sites or time windows (See US-3).
- **FR-009**: System MUST run the entire pipeline (download to statistical output) on a CPU-only environment with ≤7 GB RAM and ≤14 GB disk usage (See US-3).

### Key Entities

- **EEG Epoch**: A segment of neural data time-locked to a stimulus event, containing signal amplitude across channels.
- **Learning Block**: A grouping of 50 consecutive trials used to calculate behavioral accuracy and average MMN amplitude.
- **MMN Amplitude**: The mean voltage difference between deviant and standard responses in the 150–250ms window.
- **Behavioral Accuracy**: The percentage of correct responses within a specific learning block.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between MMN amplitude and behavioral accuracy is measured against the null hypothesis of zero correlation using a linear mixed-effects model (See FR-006, US-3).
- **SC-002**: The statistical significance of the correlation is measured against a null distribution generated by 1000 permutation tests (See FR-007, US-3).
- **SC-003**: The robustness of the threshold (150–250ms window) is measured by sweeping the window boundaries (e.g., 140–240ms, 160–260ms) and reporting the variation in the correlation coefficient (See FR-004, US-2).
- **SC-004**: The validity of the dataset-variable fit is measured by verifying that the OpenNeuro metadata explicitly contains the "stimulus type" and "response correctness" variables required for the analysis (See FR-001, US-1).
- **SC-005**: The computational feasibility is measured by ensuring the total runtime does not exceed a reasonable threshold on a 2-core CPU runner with ≤7 GB RAM (See FR-009, US-3).

## Assumptions

- **Dataset Availability**: It is assumed that OpenNeuro contains at least one public dataset with ≥20 subjects and ≥500 trials per condition that explicitly labels "standard" and "deviant" tactile stimuli and records behavioral response correctness. If no such dataset exists, the project scope is limited to a single-subject case study or requires a `[NEEDS CLARIFICATION]` on data source.
- **Methodological Validity**: It is assumed that the 150–250ms time window is a standard, validated window for somatosensory MMN in the literature, and that the 1–40 Hz filter range effectively isolates the relevant neural signals without distorting the MMN component.
- **Computational Constraints**: It is assumed that the selected datasets (raw EEG) can be fully loaded into ~7 GB RAM after downsampling or subsetting, and that MNE-Python operations (ICA, filtering) can be completed within the CI limit on a 2-core CPU.
- **Inference Framing**: It is assumed that the study design is observational (no random assignment to learning conditions), and therefore any observed correlation will be framed as ASSOCIATIONAL, not causal, in the final report.
- **Threshold Justification**: The 150–250ms window is chosen based on community standards for somatosensory MMN; a sensitivity analysis will sweep the window by ±10ms to ensure results are not an artifact of this specific boundary choice.
