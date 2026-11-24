# Feature Specification: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Feature Branch**: `001-network-centrality-sleep-synchrony`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) (US-1)

The researcher can automatically download the Sleep-EDF dataset from PhysioNet, preprocess the raw EEG signals (bandpass filtering within a low-frequency range, ICA artifact removal), and segment the data into 30‑second epochs labeled by sleep stage (Wake, N1, N2, N3, REM) and subject ID.

**Why this priority**: Without clean, segmented data for both waking and sleep states, no analysis can occur. This is the foundational step that enables all subsequent metric calculations.

**Independent Test**: The pipeline can be executed on a subset of the Sleep-EDF dataset, and the output can be verified by checking that the number of epochs matches the expected duration for each sleep stage and that no NaN values remain in the filtered signal arrays.

**Acceptance Scenarios**:

1. **Given** a valid PhysioNet account and network access, **When** the pipeline runs the download and extraction script, **Then** the Sleep-EDF .edf files are stored locally with a verified checksum.
2. **Given** raw EEG data containing artifacts, **When** the ICA cleaning module runs, **Then** components with kurtosis > 5.0 or high‑frequency power > 3× baseline are flagged and removed, ensuring artifact topographies are excluded from the signal.
3. **Given** the cleaned signal, **When** the epoching module runs, **Then** every 30‑second window is tagged with the correct sleep stage label from the accompanying annotation file.

---

### User Story 2 - Metric Computation (Centrality and Synchrony) (Priority: P2) (US-2)

The researcher can compute inter‑hemispheric coherence (average coherence between the two EEG derivations Fpz‑Cz and Pz‑Oz) from the waking resting‑state recordings (derived from theta (4‑8 Hz) and alpha (8‑13 Hz) bands) and calculate neural synchrony (Phase‑Locking Value) for each sleep stage from the segmented EEG epochs.

**Why this priority**: This generates the specific variables required to answer the research question (the predictor and the outcome). It transforms raw data into the statistical inputs needed for correlation analysis while respecting the limited EEG montage of Sleep‑EDF.

**Independent Test**: The system can generate a summary CSV containing one row per subject with columns for each coherence metric (theta‑coherence, alpha‑coherence) and each sleep‑stage synchrony score, which can be opened in a spreadsheet application without errors.

**Acceptance Scenarios**:

1. **Given** the preprocessed waking resting‑state data, **When** the connectivity matrix is constructed using theta (4‑8 Hz) and alpha (8‑13 Hz) band coherence on EEG‑only channels, **Then** the matrix is symmetric and contains values strictly between 0 and 1.
2. **Given** a synthetic test graph with known topology, **When** NetworkX eigenvector centrality algorithms run, **Then** the output values match pre‑calculated reference values within a tolerance of 1e‑6. *(Note: this scenario remains for validation of the underlying graph utilities, not for the primary predictor.)*
3. **Given** sleep‑stage epochs, **When** the Phase‑Locking Value (PLV) is calculated across electrode pairs and aggregated as mean global synchrony, **Then** the resulting synchrony score for a stage is a single float value between 0 and 1.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3) (US-3)

The researcher can execute the correlation analysis between waking inter‑hemispheric coherence and sleep synchrony, adjust for covariates, apply appropriate multiple‑comparison correction, and generate a report visualizing the significant associations (or lack thereof) across sleep stages.

**Why this priority**: This delivers the final scientific output (the answer to the research question) and ensures the statistical validity of the findings through appropriate error correction and confound adjustment.

**Independent Test**: The analysis script can be run on the generated metrics CSV, producing a JSON report that lists the correlation coefficients, raw p‑values, corrected p‑values, and covariate‑adjusted effect sizes, which can be programmatically validated for format compliance.

**Acceptance Scenarios**:

1. **Given** the metrics dataset with N ≥ 50 subjects, **When** the normality check (Shapiro‑Wilk, FR‑012) is performed, **Then** the system selects Pearson correlation if normal (p ≥ 0.05) or Spearman's rank correlation if non‑normal (p < 0.05).
2. **Given** the set of raw p‑values, **When** the Benjamini‑Hochberg FDR correction (FR‑007) is applied, **Then** the adjusted q‑values control the false discovery rate at α = 0.05.
3. **Given** the corrected results, **When** the report is generated, **Then** it explicitly flags any findings where the adjusted q‑value is < 0.05 as "Significant" and others as "Non‑Significant".
4. **Given** the subject count, **When** the analysis begins, **Then** the system validates that N ≥ 50; if N < 50, the analysis is halted and a "Insufficient Sample Size" warning is logged. (FR‑010)
5. **Given** repeated waking recordings for a subset of subjects, **When** the Intraclass Correlation (ICC) for the coherence predictor is computed (FR‑015), **Then** the pipeline proceeds only if ICC ≥ 0.6, otherwise it logs a stability warning. *(Replaces reference to non‑existent FR‑016.)*
6. **Given** the covariate data (medication status, sleep‑quality score, EEG‑noise level), **When** the regression model includes these covariates (FR‑014), **Then** the report lists adjusted effect sizes and notes any covariates with p < 0.05. *(Corrected reference to FR‑014.)*

---

### Edge Cases

- **Missing Sleep Stages**: What happens if a subject's recording lacks a specific sleep stage (e.g., no REM detected)? The system must handle this by excluding that specific stage‑subject pair from the correlation calculation rather than crashing or imputing a zero.
- **Data Corruption**: How does the system handle a corrupted Sleep‑EDF .edf file in the dataset? The pipeline must log the error, skip the specific file, and continue processing the remaining subjects without halting the entire job.
- **Collinearity**: If two centrality metrics (e.g., degree and eigenvector) are highly correlated, the system must not claim independent predictive effects but should report the joint relationships and diagnostic VIF (Variance Inflation Factor) values. *(Note: with a single coherence predictor VIF is not applicable; FR‑009 has been removed.)*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the Sleep‑EDF dataset from PhysioNet and verify file integrity via checksums before processing begins (See US-1).
- **FR-002**: System MUST apply a bandpass filter (0.5–45 Hz) and perform ICA artifact removal on all raw EEG signals, outputting a cleaned signal array (See US-1).
- **FR-003**: System MUST construct functional connectivity matrices using coherence in theta (4‑8 Hz) and alpha (8‑13 Hz) bands from the raw waking resting‑state EEG data (EEG‑only channels) (See US-2).
- **FR-004**: System MUST compute inter‑hemispheric coherence (average coherence between EEG channels Fpz‑Cz and Pz‑Oz) for each frequency band and use the resulting value(s) as the waking predictor (See US-2).
- **FR-005**: System MUST calculate the Phase‑Locking Value (PLV) across all electrode pairs for each 30‑second epoch, aggregating to a mean global synchrony score per sleep stage (See US-2).
- **FR-006**: System MUST perform correlation analysis (Pearson if normal, Spearman if non‑normal) between each waking coherence metric and each sleep‑stage synchrony score, adjusting for covariates (See US-3).
- **FR-007**: System MUST apply the Benjamini‑Hochberg FDR correction to the resulting p‑values to control the false discovery rate at α = 0.05 (See US-3).
- **FR-008**: System MUST output a final report containing correlation coefficients, raw p‑values, FDR‑adjusted q‑values, and covariate‑adjusted effect sizes for all tested pairs (See US-3).
- **FR-010**: System MUST validate the subject count (N ≥ 50) before analysis and halt with a warning if the threshold is not met (See US-3).
- **FR-011**: System MUST log the temporal proximity of waking and sleep segments and include a "Confounding Limitation" section in the report if they are from the same night (See US-2).
- **FR-012**: System MUST perform a Shapiro‑Wilk normality test on each predictor and outcome variable prior to selecting the correlation method (See US-3).
- **FR-013**: System MUST filter out any subject whose waking recording duration is < 2 minutes; only subjects meeting this minimum are retained for centrality computation (See US-1).
- **FR-014**: System MUST collect additional covariates (medication status, sleep‑quality score, EEG‑noise level) and include them as control variables in the regression model (See US-3).
- **FR-015**: System MUST compute the Intraclass Correlation (ICC) for the waking coherence predictor across available repeated recordings and proceed only if ICC ≥ 0.6 (See US-3).

### Key Entities

- **Subject**: An individual participant with both waking and sleep recordings. Key attributes: `subject_id`, `age`, `gender`.
- **WakingCoherence**: A vector containing inter‑hemispheric coherence values for theta and alpha bands. Key attributes: `theta_coherence`, `alpha_coherence`.
- **SleepStageEpoch**: A 30‑second segment of EEG data labeled with a sleep stage. Key attributes: `stage_label` (N1, N2, N3, REM), `plv_score`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The percentage of successfully processed subjects (those with complete waking and sleep data) is measured against the total number of subjects in the downloaded dataset (See US-1).
- **SC-002**: The computational runtime of the full pipeline (download to report) is measured against a target of **< 4 hours** on **standard hardware** (8‑core Intel i7‑9700K @ 3.6 GHz, 16 GB RAM, Ubuntu 22.04) using **wall‑clock time** captured via the `time` command (See US-1). *Justification*: Ensures reproducibility on typical research workstations without requiring specialized compute resources.
- **SC-003**: The memory footprint of the data processing step is measured against a target of **< 4 GB RAM** under **full load** (processing all ≥50 subjects with up to 4 parallel workers); memory is recorded as **peak RSS** using the `psutil` library (See US-1).
- **SC-004**: The statistical validity of the findings is measured against the requirement that all reported significant results have an FDR‑adjusted q‑value < 0.05 (See US-3).
- **SC-005**: The methodological soundness is measured by the presence of an ICC stability report (ICC ≥ 0.6) for the waking coherence predictor (See US-3).

## Assumptions

- The Sleep‑EDF dataset on PhysioNet contains both the required waking resting‑state recordings and the corresponding sleep‑stage annotations for a sufficient number of subjects (n ≥ 50) to achieve statistical power for medium‑effect correlations.
- **Minimum waking segment**: Only subjects with at least **2 minutes** of continuous wake recording are retained; this duration is commonly accepted as sufficient for estimating resting‑state coherence (see standard EEG resting‑state practice).
- The analysis will be observational; therefore, all reported relationships will be framed as associational, not causal, as no randomization or identification strategy is employed.
- The available CPU resources are sufficient to process the EEG data using standard Python libraries (MNE‑Python, NetworkX, SciPy) without requiring GPU acceleration or heavy model training.
- The dataset contains the necessary electrode configurations (Fpz‑Cz, Pz‑Oz) to compute coherence and PLV; if additional electrodes are missing, the analysis proceeds with the available subset.
- The Benjamini‑Hochberg FDR correction method is the chosen approach for multiple‑comparison control, assuming a standard false discovery rate of 0.05.
- The system runtime and memory usage will not exceed acceptable thresholds on standard hardware; if they do, the pipeline is considered to have failed the performance criteria.
- The ICC assessment (FR‑015) provides an empirical justification that the waking coherence predictor is stable across recordings, supporting its use as an individual‑level trait.
- Covariates (medication status, sleep‑quality score, EEG‑noise level) are available for each subject and are measured reliably; they are incorporated to reduce confounding bias.
