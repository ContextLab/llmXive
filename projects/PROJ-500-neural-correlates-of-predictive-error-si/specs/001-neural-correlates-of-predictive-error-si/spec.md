# Feature Specification: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Feature Branch**: `001-neural-correlates-tactile-learning`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does the amplitude of somatosensory mismatch negativity (MMN) attenuate as behavioral accuracy improves during tactile texture discrimination learning?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download raw EEG datasets from OpenNeuro matching specific tactile/somatosensory criteria, preprocess them (filtering, ICA, interpolation), and epoch the data into standard/deviant trials with a success rate of ≥ 95% for datasets meeting the inclusion criteria. Datasets with <20 subjects are included but flagged as underpowered.

**Why this priority**: Without clean, correctly epoched data, no analysis of MMN amplitude or behavioral alignment is possible. This is the foundational step for the entire research project.

**Independent Test**: Can be fully tested by executing the data ingestion script on a sample dataset and verifying the output contains correctly labeled epochs, filtered signals, and interpolated channels without manual intervention.

**Acceptance Scenarios**:

1. **Given** a dataset ID from OpenNeuro that meets the "tactile" and "odd-ball" search filters, **When** the ingestion script runs on a 2-core CPU runner for a single-subject dataset, **Then** the system downloads the raw data, streams/processes it using chunked buffering (never holding the full file in memory/disk simultaneously), deletes the raw file, and converts it to MNE-Python format within 15 minutes.
2. **Given** raw EEG data with known bad channels, **When** the preprocessing step runs, **Then** the system applies a low-frequency bandpass filter, removes artifacts via ICA, and interpolates bad channels, resulting in a continuous cleaned signal with artifact variance reduced by ≥20% as measured by topographic correlation.
3. **Given** a cleaned dataset, **When** the epoching step runs, **Then** the system extracts epochs from a pre-stimulus baseline period to a post-stimulus interval relative to stimulus onset, correctly separating standard and deviant stimuli based on metadata, with a trial count loss of ≤ 5% due to artifact rejection.

---

### User Story 2 - MMN Amplitude and Behavioral Alignment (Priority: P2)

The system MUST compute the somatosensory mismatch negativity (MMN) amplitude at specific somatosensory and central electrodes in the 150–250ms window and align these neural signals with behavioral accuracy calculated in fixed-length learning blocks, verifying stationarity within each block.

**Why this priority**: This step generates the core variables (neural error signal and behavioral performance) required to test the primary hypothesis. It transforms raw data into analyzable metrics.

**Independent Test**: Can be fully tested by running the alignment module on a pre-processed dataset and verifying the output CSV contains a time-series of MMN amplitudes and corresponding accuracy percentages for each block, with no missing values for valid blocks.

**Acceptance Scenarios**:

1. **Given** epoch data with standard and deviant trials, **When** the MMN calculation runs, **Then** the system computes the difference wave (deviant minus standard) and extracts the mean amplitude in the early post-stimulus window for electrodes CP3, CP4, C3, and C4.
2. **Given** behavioral response logs and trial epochs, **When** the alignment step runs, **Then** the system bins trials into fixed-size trial blocks, calculates the accuracy percentage per block, verifies that the accuracy trend within the block is <10% (stationarity check), and merges this with the corresponding MMN amplitude for that block.
3. **Given** a subject with < 10 valid trials in a specific block, **When** the alignment step runs, **Then** the system flags that block as "insufficient data" and excludes it from the final analysis dataframe to prevent noise in the correlation.

---

### User Story 3 - Statistical Modeling and Validation (Priority: P3)

The system MUST fit a Generalized Linear Mixed-Effects Model (GLMM) with a beta distribution to test the correlation between MMN amplitude and behavioral accuracy including a Learning_Phase interaction, apply a multiple-comparison correction for the four specified electrodes, and run a permutation test (n=1000) to validate significance.

**Why this priority**: This provides the statistical evidence for the research question. It moves from descriptive data to inferential conclusions, addressing the core "Does X attenuate as Y improves?" question with appropriate statistical rigor for bounded proportion data.

**Independent Test**: Can be fully tested by executing the analysis script on the aligned dataset and verifying the output includes the model coefficients, p-values (corrected), and a permutation test p-value, all generated within 6 hours on CPU-only hardware.

**Acceptance Scenarios**:

1. **Given** the aligned dataset with MMN amplitudes and accuracy per block, **When** the statistical model runs, **Then** the system fits a GLMM with "Accuracy" and "Learning_Phase" (including interaction term) as fixed effects and "Subject" as the random intercept, outputting the slope coefficient and p-value.
2. **Given** a p-value < 0.05 from the initial model, **When** the validation step runs, **Then** the system performs a permutation test with a sufficient number of shuffles of the accuracy labels and reports the empirical p-value.
3. **Given** a result where the observed statistic falls within the top [deferred] of the null distribution, **When** the validation step completes, **Then** the system flags the result as "statistically significant (p < 0.05)" in the final report.

### Edge Cases

- What happens when an OpenNeuro dataset has missing metadata for stimulus types (standard vs. deviant)? The system MUST log a warning and skip that specific dataset, rather than crashing.
- How does the system handle a subject with zero behavioral accuracy in all blocks? The system MUST exclude that subject from the GLMM to avoid singularity issues in the regression.
- How does the system handle datasets where the 150–250ms window contains no data (e.g., due to excessive artifact rejection)? The system MUST mark the MMN amplitude for that block as NaN and exclude it from the correlation analysis.
- What happens if behavioral response logs are missing? The system MUST fall back to calculating "Stimulus-Driven MMN" (based on probability) and flag the analysis as "Stimulus-Driven, not Error-Signal" in the output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse raw EEG data from OpenNeuro for datasets matching the "tactile", "somatosensory", and "odd-ball" filters; datasets with <20 subjects MUST be included but flagged as underpowered (See US-1).
- **FR-002**: System MUST apply a bandpass filter with a lower cutoff frequency in the low-frequency range to isolate relevant signal components., perform ICA-based artifact removal, and interpolate bad channels using MNE-Python (See US-1).
- **FR-003**: System MUST epoch data from a pre-stimulus baseline period to a defined post-stimulus window and separate standard/deviant trials based on protocol metadata (See US-1).
- **FR-004**: System MUST compute MMN amplitude as the mean difference wave (deviant minus standard) in the early-latency window at electrodes CP3, CP4, C3, and C4 (See US-2).
- **FR-005**: System MUST segment behavioral data into fixed-size trial bins, calculate accuracy per bin, and verify stationarity (accuracy trend <10%) within each bin before alignment (See US-2).
- **FR-006**: System MUST fit a Generalized Linear Mixed-Effects Model (GLMM) with beta distribution: `MMN ~ Accuracy * Learning_Phase + (1|Subject)` to test the correlation (See US-3).
- **FR-007**: System MUST perform a permutation test (n=1000) to validate the significance of the correlation against a null distribution (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) for the four specified electrode sites (CP3, CP4, C3, C4) (See US-3).
- **FR-009**: System MUST run the entire pipeline (download to statistical output) on a CPU-only environment with ≤7 GB RAM and ≤14 GB disk usage (peak temporary buffer only, excluding raw source) for the maximum expected load (20 subjects, ≥500 trials) (See US-3).
- **FR-010**: System MUST perform a sensitivity analysis sweeping the time window boundaries (e.g., early-to-mid latency ranges) and report the variation in the correlation coefficient (See US-3).
- **FR-011**: System MUST detect if behavioral response logs are missing and automatically switch to calculating "Stimulus-Driven MMN" (based on stimulus probability) while flagging the result as "Stimulus-Driven" (See US-2).
- **FR-012**: System MUST distinguish between "Error-Signal MMN" (derived from accuracy logs) and "Stimulus-Driven MMN" (derived from stimulus probability) in all output reports (See US-2).

### Key Entities

- **EEG Epoch**: A segment of neural data time-locked to a stimulus event, containing signal amplitude across channels.
- **Learning Block**: A grouping of 10 consecutive trials used to calculate behavioral accuracy and average MMN amplitude.
- **MMN Amplitude**: The mean voltage difference between deviant and standard responses in the 150–250ms window.
- **Behavioral Accuracy**: The percentage of correct responses within a specific learning block.
- **Learning Phase**: An ordinal variable representing the progression of the learning task (e.g., Block 1, Block 2, etc.).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between MMN amplitude and behavioral accuracy is measured against the null hypothesis of zero correlation using a GLMM (See FR-006, US-3).
- **SC-002**: The statistical significance of the correlation is measured against a null distribution generated by a sufficient number of permutation tests. (See FR-007, US-3).
- **SC-003**: The robustness of the threshold (150–250ms window) is measured by sweeping the window boundaries (e.g., 140–240ms, 160–260ms) and reporting the variation in the correlation coefficient (See FR-010, US-3).
- **SC-004**: The validity of the dataset-variable fit is measured by verifying that the OpenNeuro metadata explicitly contains the "stimulus type" and "response correctness" variables required for the analysis (See FR-001, US-1).
- **SC-005**: The computational feasibility is measured by ensuring the total runtime does not exceed 6 hours on a 2-core CPU runner with ≤7 GB RAM (See FR-009, US-3).

## Assumptions

- **Dataset Availability**: It is assumed that OpenNeuro contains public datasets with tactile/somatosensory odd-ball tasks. If behavioral response logs are missing, the project will proceed with "Stimulus-Driven MMN" analysis, noting this limitation as a fallback strategy rather than a blocker. If no dataset exists with ≥20 subjects, smaller datasets are included but flagged as underpowered.
- **Methodological Validity**: It is assumed that the An early time window is a standard, validated window for somatosensory MMN in the literature, and that the A low-frequency filter range effectively isolates the relevant neural signals without distorting the MMN component..
- **Computational Constraints**: It is assumed that the selected datasets (raw EEG) can be fully loaded into a standard RAM capacity after downsampling or subsetting, and that MNE-Python operations (ICA, filtering) can be completed within the CI limit on a 2-core CPU.
- **Inference Framing**: It is assumed that the study design is observational (no random assignment to learning conditions), and therefore any observed correlation will be framed as ASSOCIATIONAL, not causal, in the final report.
- **Threshold Justification**: The 150–250ms window is chosen based on community standards for somatosensory MMN; a sensitivity analysis will sweep the window by ±10ms to ensure results are not an artifact of this specific boundary choice.