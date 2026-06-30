# Feature Specification: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Feature Branch**: `001-network-centrality-sleep-synchrony`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher can automatically download the Sleep-EDF dataset from PhysioNet, preprocess the raw EEG signals (bandpass filtering within a low-frequency range, ICA artifact removal), and segment the data into 30-second epochs labeled by sleep stage (Wake, N1, N2, N3, REM) and subject ID.

**Why this priority**: Without clean, segmented data for both waking and sleep states, no analysis can occur. This is the foundational step that enables all subsequent metric calculations.

**Independent Test**: The pipeline can be executed on a subset of the Sleep-EDF dataset, and the output can be verified by checking that the number of epochs matches the expected duration for each sleep stage and that no NaN values remain in the filtered signal arrays.

**Acceptance Scenarios**:

1. **Given** a valid PhysioNet account and network access, **When** the pipeline runs the download and extraction script, **Then** the Sleep-EDF .edf files are stored locally with a verified checksum.
2. **Given** raw EEG data containing artifacts, **When** the ICA cleaning module runs, **Then** components with kurtosis > 5.0 or high-frequency power > 3x baseline are flagged and removed, ensuring artifact topographies are excluded from the signal.
3. **Given** the cleaned signal, **When** the epoching module runs, **Then** every 30-second window is tagged with the correct sleep stage label from the accompanying annotation file.

---

### User Story 2 - Metric Computation (Centrality and Synchrony) (Priority: P2)

The researcher can compute network centrality metrics (degree, betweenness, eigenvector) from the waking resting-state functional connectivity matrices (derived from theta (4-8 Hz) and alpha (8-13 Hz) bands) and calculate neural synchrony (Phase Lag Index) for each sleep stage from the segmented EEG epochs.

**Why this priority**: This generates the specific variables required to answer the research question (the predictor and the outcome). It transforms raw data into the statistical inputs needed for correlation analysis.

**Independent Test**: The system can generate a summary CSV containing one row per subject with columns for each centrality metric and each sleep-stage synchrony score, which can be opened in a spreadsheet application without errors.

**Acceptance Scenarios**:

1. **Given** the preprocessed waking resting-state data, **When** the connectivity matrix is constructed using theta (4-8 Hz) and alpha (8-13 Hz) band coherence, **Then** the matrix is symmetric and contains values strictly between 0 and 1.
2. **Given** a synthetic test graph with known topology, **When** NetworkX eigenvector centrality algorithms run, **Then** the output values match pre-calculated reference values within a tolerance of 1e-6.
3. **Given** sleep-stage epochs, **When** the Phase Lag Index (PLI) is calculated across electrode pairs and aggregated as mean global synchrony, **Then** the resulting synchrony score for a stage is a single float value between 0 and 1.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The researcher can execute the correlation analysis between waking centrality and sleep synchrony, apply Bonferroni correction for multiple comparisons, and generate a report visualizing the significant associations (or lack thereof) across sleep stages.

**Why this priority**: This delivers the final scientific output (the answer to the research question) and ensures the statistical validity of the findings through appropriate error correction.

**Independent Test**: The analysis script can be run on the generated metrics CSV, producing a JSON report that lists the correlation coefficients, p-values, and corrected p-values, which can be programmatically validated for format compliance.

**Acceptance Scenarios**:

1. **Given** the metrics dataset with N=30 subjects, **When** the normality check (Shapiro-Wilk) is performed, **Then** the system selects Pearson correlation if normal (p >= 0.05) or Spearman's rank correlation if non-normal (p < 0.05).
2. **Given** the set of raw p-values, **When** the Bonferroni correction is applied, **Then** the adjusted p-values are strictly greater than or equal to the raw p-values, and the family-wise error rate is controlled.
3. **Given** the corrected results, **When** the report is generated, **Then** it explicitly flags any findings where the adjusted p-value is < 0.05 as "Significant" and others as "Non-Significant".
4. **Given** the subject count, **When** the analysis begins, **Then** the system validates that N >= 30; if N < 30, the analysis is halted and a "Insufficient Sample Size" warning is logged.

### Edge Cases

- **Missing Sleep Stages**: What happens if a subject's recording lacks a specific sleep stage (e.g., no REM detected)? The system must handle this by excluding that specific stage-subject pair from the correlation calculation rather than crashing or imputing a zero.
- **Data Corruption**: How does the system handle a corrupted Sleep-EDF .edf file in the dataset? The pipeline must log the error, skip the specific file, and continue processing the remaining subjects without halting the entire job.
- **Collinearity**: If two centrality metrics (e.g., degree and eigenvector) are highly correlated, the system must not claim independent predictive effects but should report the joint relationships and diagnostic VIF (Variance Inflation Factor) values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the Sleep-EDF dataset from PhysioNet and verify file integrity via checksums before processing begins (See US-1).
- **FR-002**: System MUST apply a bandpass filter (0.5–45 Hz) and perform ICA artifact removal on all raw EEG signals, outputting a cleaned signal array (See US-1).
- **FR-003**: System MUST construct functional connectivity matrices using coherence in theta (4-8 Hz) and alpha (8-13 Hz) bands from the raw waking resting-state EEG data (See US-2).
- **FR-004**: System MUST compute degree, betweenness, and eigenvector centrality metrics for every node in the waking network using NetworkX (See US-2).
- **FR-005**: System MUST calculate the Phase Lag Index (PLI) across all electrode pairs for each 30-second epoch, aggregating to a mean global synchrony score per sleep stage (See US-2).
- **FR-006**: System MUST perform correlation analysis (Pearson if normal, Spearman if non-normal) between each centrality metric and each sleep-stage synchrony score, stratified by stage (See US-3).
- **FR-007**: System MUST apply Bonferroni correction to the resulting p-values to control for family-wise error rate across all tested hypotheses (See US-3).
- **FR-008**: System MUST output a final report containing correlation coefficients, raw p-values, and corrected p-values for all tested pairs (See US-3).
- **FR-009**: System MUST calculate Variance Inflation Factor (VIF) for all centrality metrics and report values > 5.0 as collinear (See US-2).
- **FR-010**: System MUST validate the subject count (N >= 30) before analysis and halt with a warning if the threshold is not met (See US-3).
- **FR-011**: System MUST log the temporal proximity of waking and sleep segments and include a "Confounding Limitation" section in the report if they are from the same night (See US-2).
- **FR-012**: System MUST perform a Shapiro-Wilk normality test on the correlation variables and select the appropriate correlation method (Pearson or Spearman) based on the result (See US-3).

### Key Entities

- **Subject**: An individual participant with both waking and sleep recordings. Key attributes: `subject_id`, `age`, `gender`.
- **WakingNetwork**: A functional connectivity graph derived from resting-state EEG. Key attributes: `connectivity_matrix`, `centrality_metrics` (degree, betweenness, eigenvector).
- **SleepStageEpoch**: A 30-second segment of EEG data labeled with a sleep stage. Key attributes: `stage_label` (N1, N2, N3, REM), `plv_score`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The percentage of successfully processed subjects (those with complete waking and sleep data) is measured against the total number of subjects in the downloaded dataset (See US-1).
- **SC-002**: The computational runtime of the full pipeline (download to report) is measured against a target of < 4 hours on standard hardware (See Assumptions).
- **SC-003**: The memory footprint of the data processing step is measured against a target of < 4 GB RAM under full load (See Assumptions).
- **SC-004**: The statistical validity of the findings is measured against the requirement that all reported significant results have a Bonferroni-corrected p-value < 0.05 (See US-3).
- **SC-005**: The methodological soundness is measured by the presence of a collinearity diagnostic (VIF) report when multiple centrality metrics are analyzed (See US-2).

## Assumptions

- The Sleep-EDF dataset on PhysioNet contains both the required waking resting-state recordings and the corresponding sleep-stage annotations for a sufficient number of subjects (n ≥ 30) to achieve statistical power for medium-effect correlations.
- The analysis will be observational; therefore, all reported relationships will be framed as associational, not causal, as no randomization or identification strategy is employed.
- The available CPU resources are sufficient to process the EEG data. using standard Python libraries (MNE-Python, NetworkX, SciPy) without requiring GPU acceleration or heavy model training.
- The dataset contains the necessary electrode configurations to compute coherence and PLI; if specific electrodes are missing, the analysis will proceed with the available subset.
- The Bonferroni correction method is the chosen approach for multiple comparison control, assuming a standard alpha level of 0.05.
- The system runtime and memory usage will not exceed acceptable thresholds on standard hardware; if they do, the pipeline is considered to have failed the performance criteria.