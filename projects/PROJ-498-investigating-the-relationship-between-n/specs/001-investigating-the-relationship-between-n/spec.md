# Feature Specification: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Feature Branch**: `001-investigating-neural-synchrony-attention-switching`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Neural Synchrony and Attention Switching Costs"

## User Scenarios & Testing

### User Story 1 - Preprocess and Epoch Public Task-Switching EEG Data (Priority: P1)

The researcher downloads the OpenNeuro task-switching dataset (e.g., dsXXXX) and preprocesses it to create clean, time-locked epochs suitable for analysis. This includes bandpass filtering (1–45 Hz), ICA-based artifact removal, and epoching around stimulus onset (-1000ms to +2000ms).

**Why this priority**: This is the foundational step; without clean, correctly epoch-aligned data, no synchrony or behavioral analysis can occur. It validates the data pipeline's ability to handle the specific dataset constraints on a CPU-only environment.

**Independent Test**: Can be fully tested by running the preprocessing script on a single subject and verifying the output contains valid epoch objects with the correct time window and no NaN artifacts.

**Acceptance Scenarios**:

1. **Given** a raw EEG file from the target dataset, **When** the preprocessing pipeline runs, **Then** the output contains epochs time-locked to stimulus onset with a duration of 3000ms (-1000ms to +2000ms).
2. **Given** raw data containing muscle artifacts, **When** ICA-based removal is applied, **Then** the system identifies and removes ICA components exhibiting a kurtosis > 5 or a spectral peak > 30 Hz, while preserving components below these thresholds.
3. **Given** the computational constraint of 7GB RAM, **When** processing a single subject sequentially, **Then** the memory usage does not exceed 6.5 GB, ensuring the process does not crash on the free-tier runner.

---

### User Story 2 - Compute Pre-Stimulus Frontoparietal Synchrony Metrics (Priority: P2)

The researcher calculates Phase-Locking Value (PLV) or weighted Phase-Lag Index (wPLI) between frontoparietal electrode pairs (approximating DLPFC and parietal cortex) in the pre-stimulus window (-500ms to 0ms) for theta (4–7 Hz) and gamma (30–45 Hz) bands.

**Why this priority**: This is the core predictor generation. It transforms raw signals into the specific metric hypothesized to predict behavior. It must run without GPU acceleration.

**Independent Test**: Can be fully tested by computing PLV on a synthetic signal with known phase relationships and verifying the output matches the theoretical expectation within a tolerance of 0.05.

**Acceptance Scenarios**:

1. **Given** epoched data with valid frontoparietal channels, **When** the synchrony calculation runs for the -500ms to 0ms window, **Then** the output includes a matrix of PLV/wPLI values for theta and gamma bands.
2. **Given** the absence of an individual MRI, **When** source localization is approximated, **Then** the system maps electrodes F3/F4, FC3/FC4 to DLPFC and P3/P4, CP3/CP4 to parietal regions using the standard 10-20 montage. The system acknowledges that these scalp-level measures are proxies for inter-areal coupling and rely on wPLI to mitigate volume conduction effects.
3. **Given** the CPU constraint, **When** calculating synchrony for a single subject, **Then** the computation completes in ≤ 30 minutes per subject.

---

### User Story 3 - Correlate Synchrony with Behavioral Switching Costs (Priority: P3)

The researcher computes attention switching costs (RT_switch - RT_stay) per subject and correlates these with mean pre-stimulus synchrony using mixed-effects models or permutation testing to determine statistical significance. This includes both a primary subject-level analysis and a secondary trial-level mixed-effects analysis.

**Why this priority**: This delivers the final research answer. It connects the neural predictor to the behavioral outcome, validating the hypothesis.

**Independent Test**: Can be fully tested by running the correlation analysis on a mock null dataset (randomly shuffled synchrony and RT) and verifying the Type I error rate (p < 0.05) does not exceed 5% across 1000 iterations.

**Acceptance Scenarios**:

1. **Given** subject-level synchrony means and behavioral switching costs, **When** the correlation analysis runs, **Then** the output includes a Pearson/Spearman correlation coefficient and a p-value derived from 1000 permutation iterations.
2. **Given** multiple hypothesis tests (e.g., testing both theta and gamma bands), **When** the statistical test runs, **Then** a multiple-comparison correction (e.g., Bonferroni or FDR) is applied to the p-values.
3. **Given** the observational nature of the data, **When** the results are formatted, **Then** the output explicitly frames findings as associational rather than causal.
4. **Given** trial-level data, **When** the secondary analysis runs, **Then** a linear mixed-effects model correlates trial-by-trial synchrony with trial-by-trial RT, accounting for subject-level random intercepts.

---

### Edge Cases

- What happens when a subject has fewer than 10 valid trials in either the switch or stay condition? System MUST exclude the subject from the correlation analysis and log the exclusion to `exclusions.csv` with the reason "insufficient trials".
- How does the system handle subjects where the ICA component removal removes >50% of the data? System MUST flag the subject as low-quality, write a warning to `exclusions.csv` with the reason "excessive artifact removal", and exclude the subject from the final correlation.
- What if the pre-stimulus window contains significant line noise (50/60Hz) that cannot be filtered out? System MUST apply a notch filter and log the intervention to the processing log.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and cache the specified OpenNeuro dataset (e.g., a designated dsXXXXX identifier) to a local temporary directory, ensuring no network calls occur during the analysis phase. (See US-1)
- **FR-002**: System MUST apply a 1–45 Hz bandpass filter and perform ICA-based artifact removal on the EEG data before epoching, rejecting components with kurtosis > 5 or spectral peaks > 30 Hz. (See US-1)
- **FR-003**: System MUST compute Phase-Locking Value (PLV) or weighted Phase-Lag Index (wPLI) between frontoparietal electrode pairs in the -500ms to 0ms pre-stimulus window for theta (4–7 Hz) and gamma (30–45 Hz) bands. (See US-2)
- **FR-004**: System MUST calculate the attention switching cost for each subject as the mean reaction time difference between switch and stay trials. (See US-3)
- **FR-005**: System MUST execute the final correlation analysis using 1000 permutations to assess significance and apply a multiple-comparison correction for the number of frequency bands tested. (See US-3)
- **FR-006**: System MUST run entirely on CPU without requiring CUDA, 8-bit quantization, or GPU acceleration. (See US-1, US-2, US-3)
- **FR-007**: System MUST execute a sensitivity analysis by re-running the primary correlation with pre-stimulus windows shifted to [-600ms, 0ms] and [-400ms, 0ms], verifying stability of results. (See US-3)
- **FR-008**: System MUST report all findings as associational rather than causal in the final output. (See US-3)
- **FR-009**: System MUST perform a secondary trial-level mixed-effects analysis correlating trial-by-trial synchrony with trial-by-trial RT. (See US-3)

### Key Entities

- **EEG Epoch**: A time-locked segment of EEG data (-1000ms to +2000ms) associated with a specific trial type (switch/stay).
- **Synchrony Metric**: A scalar value (PLV or wPLI) representing the phase consistency between two electrode pairs in a specific frequency band.
- **Switching Cost**: A scalar value representing the behavioral penalty (in ms) for switching task sets.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The preprocessing pipeline's peak RSS is measured against the target of ≤ 6.5 GB to ensure no OOM errors occur on the GitHub Actions free-tier runner. (See FR-002, FR-006)
- **SC-002**: The total analysis runtime (download to final correlation) is measured against the target of ≤ 6 hours. (See FR-006)
- **SC-003**: The statistical validity of the correlation is measured against the requirement for a multiple-comparison correction when testing >1 frequency band. (See FR-005)
- **SC-004**: The methodological soundness of the threshold is measured against the sensitivity analysis defined in FR-007, where the correlation coefficient r must not change by > 0.1 and the p-value must remain < 0.05 across the shifted windows. (See FR-007)
- **SC-005**: The inferential framing of the results is measured against the requirement to report findings as associational rather than causal as mandated in FR-008. (See FR-008)

## Assumptions

- The OpenNeuro dataset ds004173 (or a similar task-switching dataset) contains sufficient trial counts (≥20 per condition) and clean EEG data for at least 10 subjects to allow for meaningful statistical correlation.
- The standard 10-20 electrode montage (F3/F4, P3/P4, etc.) provides a sufficient proxy for DLPFC and parietal cortex activity without requiring individual MRI source localization, acknowledging that scalp-level synchrony is a noisy proxy for inter-areal coupling.
- The pre-stimulus window of -500ms to 0ms is the standard community window for assessing pre-stimulus neural states in this domain; no other window is considered without a sensitivity analysis.
- The dataset contains valid reaction time logs for both switch and stay trials; if a subject has missing behavioral data, they are excluded from the analysis.
- The analysis assumes a negative correlation (higher synchrony = lower cost) as the primary hypothesis, but the code must be agnostic to the direction of the correlation.
- The multiple-comparison correction method (e.g., Bonferroni) is sufficient for the two frequency bands (theta, gamma) tested; if more bands are added later, the correction logic must be updated.
- The sensitivity analysis for the pre-stimulus window boundaries (e.g., ±100ms) is computationally trivial and will be performed to validate the robustness of the primary finding.
- The target of 1000 permutations in FR-005 is the standard; if runtime exceeds limits, the system may fallback to 500 permutations, but this fallback must be logged and noted in the final report.