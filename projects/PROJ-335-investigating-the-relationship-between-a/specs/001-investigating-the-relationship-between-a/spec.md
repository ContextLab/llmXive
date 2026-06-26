# Feature Specification: Alpha Oscillations and Working Memory Capacity

**Feature Branch**: `001-alpha-oscillations-wm-capacity`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Alpha Oscillations and Working Memory Capacity"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and preprocess EEG datasets from OpenNeuro (Priority: P1)

The researcher downloads publicly available EEG datasets containing working memory tasks and preprocesses them using MNE-Python to prepare for analysis.

**Why this priority**: This is the foundational step—without cleaned EEG data and behavioral measures, no analysis can proceed. This delivers the minimum viable dataset for the research pipeline.

**Independent Test**: Can be fully tested by verifying that (1) at least one OpenNeuro dataset is successfully downloaded, (2) EEG data is bandpass-filtered (1-40 Hz), (3) artifacts are removed via ICA, and (4) trial epochs are segmented with behavioral performance scores extracted.

**Acceptance Scenarios**:

1. **Given** an OpenNeuro dataset URL (e.g., ds000246 or ds003474), **When** the download script executes, **Then** the EEG data files are saved locally with metadata intact
2. **Given** raw EEG recordings, **When** MNE-Python preprocessing runs, **Then** the output includes bandpass-filtered data (1-40 Hz), ICA-cleaned signals, and epoch-locked trials with behavioral scores
3. **Given** a dataset that lacks required behavioral measures (e.g., no k-scores or d' values), **When** the preprocessing script validates the data, **Then** the script flags `[NEEDS CLARIFICATION]` and halts rather than proceeding with incomplete variables

---

### User Story 2 - Extract alpha-band power and phase-locking metrics (Priority: P2)

The researcher computes alpha-band (8-12 Hz) power from frontal and parietal electrodes and calculates pairwise phase-locking values (PLV) between frontal-parietal sites during task delay periods.

**Why this priority**: This implements the core predictor variables (alpha power, PLV) that will be correlated with working memory capacity. It builds on the preprocessed data from US-1 and enables the statistical analysis in US-3.

**Independent Test**: Can be fully tested by verifying that (1) alpha power is extracted from at least 6 electrodes (F3, F4, Fz, P3, P4, Pz), (2) PLV is computed using Hilbert transform for frontal-parietal pairs, and (3) metrics are stored per participant for correlation analysis.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG epochs from a working memory task, **When** alpha-band power extraction runs, **Then** power values are computed for each delay period at the specified frontal and parietal electrodes
2. **Given** time-series data from frontal-parietal electrode pairs, **When** PLV calculation executes, **Then** phase-locking values are stored for each participant with electrode pair identifiers
3. **Given** incomplete electrode data (e.g., missing Pz), **When** the extraction script validates, **Then** it logs a warning but continues with available electrodes, recording which sites were excluded

---

### User Story 3 - Perform correlation analysis and robustness validation (Priority: P3)

The researcher conducts Pearson/Spearman correlation analyses between alpha metrics and working memory capacity, applies Bonferroni correction for multiple comparisons, and validates results via split-half reliability and permutation testing.

**Why this priority**: This delivers the final scientific findings—correlation coefficients, effect sizes, and robustness assessments. It depends on US-1 and US-2 being complete.

**Independent Test**: Can be fully tested by verifying that (1) correlation coefficients and p-values are computed between alpha power/PLV and working memory capacity, (2) Bonferroni correction is applied across all tested comparisons, and (3) split-half reliability and permutation tests are executed with reported confidence intervals.

**Acceptance Scenarios**:

1. **Given** alpha power and PLV metrics per participant, **When** correlation analysis runs, **Then** Pearson/Spearman coefficients are computed with p-values and 95% confidence intervals
2. **Given** multiple hypothesis tests (e.g., across 6 electrodes × 2 metrics), **When** Bonferroni correction is applied, **Then** adjusted p-values are reported and findings are framed as associational (not causal)
3. **Given** the full dataset, **When** split-half reliability and permutation testing execute, **Then** robustness metrics are output showing whether findings persist across data splits and randomizations

---

### Edge Cases

- What happens when an OpenNeuro dataset lacks behavioral performance measures (k-scores or d') needed for working memory capacity calculation?
- How does the system handle EEG datasets with insufficient trial counts (<20 trials per condition) for reliable alpha power estimation?
- What if alpha-band power and PLV are definitionally related (collinearity), making independent predictive effects impossible to claim?
- How does the system behave if the 6-hour GitHub Actions runner limit is exceeded during preprocessing?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download EEG datasets from OpenNeuro (e.g., ds000246, ds003474) containing working memory tasks with behavioral performance measures (See US-1)
- **FR-002**: System MUST preprocess EEG data using MNE-Python: bandpass filter (1-40 Hz), remove artifacts via ICA, re-reference to average mastoids, segment into trial epochs aligned to task events (See US-1)
- **FR-003**: System MUST extract alpha-band (8-12 Hz) power from at least 6 electrodes (F3, F4, Fz, P3, P4, Pz) during delay periods (See US-2)
- **FR-004**: System MUST compute pairwise phase-locking values (PLV) between frontal-parietal electrode pairs using the Hilbert transform method (See US-2)
- **FR-005**: System MUST perform Pearson/Spearman correlation analyses between alpha metrics and working memory capacity estimates, with Bonferroni correction for multiple comparisons across electrode sites (See US-3)

### Key Entities *(include if feature involves data)*

- **EEG Dataset**: Publicly available EEG recordings from OpenNeuro containing working memory tasks; key attributes: dataset ID, electrode layout, sampling rate, behavioral measures
- **Alpha Power Metric**: Computed power values in the 8-12 Hz band per electrode per participant; key attributes: electrode site, trial ID, participant ID, power value
- **PLV Metric**: Phase-locking values between electrode pairs per participant; key attributes: electrode pair, participant ID, PLV value
- **Working Memory Capacity**: Behavioral performance estimate (k-scores or d') per participant; key attributes: participant ID, capacity estimate, task type

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Alpha power and PLV correlation coefficients are measured against the expected effect size range from existing literature (See US-3)
- **SC-002**: Split-half reliability coefficients are measured against the threshold of ≥0.7 to confirm findings are robust across data subsets (See US-3)
- **SC-003**: Multiple-comparison correction is measured against the Bonferroni-adjusted family-wise error rate to control false positives across all tested electrode-site combinations (See US-3)
- **SC-004**: Dataset-variable fit is measured against the requirement that every predictor (alpha power, PLV) and outcome (working memory capacity) variable is present in the source OpenNeuro dataset (See US-1)

## Assumptions

- The OpenNeuro datasets (ds000246, ds003474) contain both EEG recordings with frontal/parietal electrode coverage AND behavioral performance measures (k-scores or d') needed to compute working memory capacity
- Findings will be framed as associational rather than causal, as this is an observational study without random assignment to conditions
- Sample size will be sufficient for correlation analyses with power ≥0.80; if the available dataset yields N<30, this limitation will be explicitly acknowledged in results
- MNE-Python preprocessing will run within the GitHub Actions free-tier limit; if preprocessing exceeds this, the dataset will be sampled to reduce trial count while maintaining ≥20 trials per condition
- Alpha power and PLV may exhibit collinearity (both derive from the same EEG signal); the analysis will report joint relationships descriptively and include a variance inflation factor (VIF) diagnostic to assess multicollinearity
- No GPU/CUDA is required; all computations (filtering, ICA, Hilbert transform, correlation) are CPU-tractable and will execute on the GitHub Actions free runner with limited CPU and memory resources
