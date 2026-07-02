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
3. **Given** a dataset that lacks required behavioral measures (e.g., no k-scores or d' values), **When** the preprocessing script validates the data, **Then** the script exits with code 1 and logs 'ERROR: Missing behavioral measures (k-scores or d') in dataset [ID]. Halting.'

---

### User Story 2 - Extract alpha-band power and phase-locking metrics (Priority: P2)

The researcher computes alpha-band power from frontal and parietal electrodes and calculates pairwise phase-locking values (PLV) between frontal-parietal sites during task delay periods.

**Why this priority**: This implements the core predictor variables (alpha power, PLV) that will be correlated with working memory capacity. It builds on the preprocessed data from US-1 and enables the statistical analysis in US-3.

**Independent Test**: Can be fully tested by verifying that (1) alpha power is extracted from at least 6 electrodes (F3, F4, Fz, P3, P4, Pz), (2) PLV is computed using Hilbert transform for frontal-parietal pairs, and (3) metrics are stored per participant for correlation analysis.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG epochs from a working memory task, **When** alpha-band power extraction runs, **Then** power values are computed for each delay period at the specified frontal and parietal electrodes
2. **Given** time-series data from frontal-parietal electrode pairs, **When** PLV calculation executes, **Then** phase-locking values are stored for each participant with electrode pair identifiers
3. **Given** incomplete electrode data (e.g., missing Pz), **When** the extraction script validates, **Then** it exits with code 1 and logs 'CRITICAL: Missing required electrode data for [list]. No partial analysis proceeds.'

---

### User Story 3 - Perform correlation analysis and robustness validation (Priority: P3)

The researcher conducts partial correlation analyses (controlling for collinearity) and cross-validated correlations between alpha metrics and working memory capacity, applies Cluster-Based Permutation Testing or FDR correction, and validates results via split-half reliability.

**Why this priority**: This delivers the final scientific findings—correlation coefficients, effect sizes, and robustness assessments—while addressing statistical dependencies and multiple comparison issues. It depends on US-1 and US-2 being complete.

**Independent Test**: Can be fully tested by verifying that (1) partial correlations or multivariate models are computed to disentangle alpha power and PLV, (2) cross-validation is used for trial-level predictions, (3) Cluster-Based Permutation Testing (α ≤ 0.05) or FDR (q ≤ 0.05) is applied, and (4) split-half reliability is reported.

**Acceptance Scenarios**:

1. **Given** alpha power and PLV metrics per participant, **When** correlation analysis runs, **Then** partial correlations (controlling for the other metric) and cross-validated correlations are computed with p-values and 95% confidence intervals
2. **Given** multiple hypothesis tests (multiple tests: multiple electrodes × 2 metrics), **When** correction is applied, **Then** Cluster-Based Permutation Testing (Maris & Oostenveld,) or FDR (q ≤ 0.05) is used, and findings are framed as associational (not causal)
3. **Given** the full dataset, **When** split-half reliability executes, **Then** robustness metrics are output showing whether findings persist across data splits

---

### Edge Cases

- What happens when an OpenNeuro dataset lacks behavioral performance measures (k-scores or d') needed for working memory capacity calculation? (Handled by FR-006 and US-1 halt)
- How does the system handle EEG datasets with insufficient trial counts (<20 trials per condition) for reliable alpha power estimation? (Handled by FR-002 validation)
- What if alpha-band power and PLV are definitionally related (collinearity), making independent predictive effects impossible to claim? (Handled by FR-009: VIF check and PCA fallback)
- How does the system behave if the -hour GitHub Actions runner limit is exceeded during preprocessing? (Handled by Assumption: sample reduction with ≥20 trials per condition)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download EEG datasets from OpenNeuro (e.g., ds, ds003474) containing working memory tasks with behavioral performance measures (See US-1)
- **FR-002**: System MUST preprocess EEG data using MNE-Python: bandpass filter (1-40 Hz), remove artifacts via ICA, re-reference to average mastoids, segment into trial epochs aligned to task events (See US-1)
- **FR-003**: System MUST extract alpha-band (8-12 Hz) power from at least 6 electrodes (F3, F4, Fz, P3, P4, Pz) during delay periods (See US-2)
- **FR-004**: System MUST compute pairwise phase-locking values (PLV) between frontal-parietal electrode pairs using the Hilbert transform method (See US-2)
- **FR-005**: System MUST perform Pearson/Spearman correlation analyses between alpha-band power/PLV metrics and working memory capacity estimates (k-scores or d'), with correction for multiple comparisons across all tested dimensions (6 electrodes × 2 metrics = 12 tests), using Cluster-Based Permutation Testing (Maris & Oostenveld,) with α ≤ 0.05, or FDR correction (q ≤ 0.05) if cluster assumptions are not met (See US-3)
- **FR-006**: System MUST validate presence of all required variables (EEG channels, k-scores/d', trial timestamps) before processing; if any are missing, the system MUST halt with a specific error code (See US-1)
- **FR-007**: System MUST compute partial correlations (controlling for the other metric) or run a multivariate model (e.g., SEM) to disentangle shared variance between alpha power and PLV before reporting independent effects (See US-3)
- **FR-008**: System MUST implement a leave-one-trial-out or split-half cross-validation approach when correlating trial-level EEG metrics with behavioral outcomes to ensure the link is not driven by trial-specific noise (See US-3)
- **FR-009**: System MUST compute Variance Inflation Factor (VIF) or perform PCA on alpha power and PLV metrics before correlation analysis. If VIF > 5, the system MUST flag collinearity and report PCA components instead of raw metrics (See US-3)

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

- **SC-001**: Correlation coefficients are measured against a threshold of |r| ≥ 0.3 (based on standard meta-analytic effect sizes for alpha-WM relationships, e.g., Klimesch et al.) to confirm meaningful association (See US-3)
- **SC-002**: Split-half reliability coefficients are measured against the threshold of ≥0.7 to confirm findings are robust across data subsets (See US-3)
- **SC-003**: Multiple-comparison correction is measured against the Cluster-Based Permutation Testing (α ≤ 0.05) or FDR (q ≤ 0.05) protocol to control false positives across all tested electrode-site combinations (See US-3)
- **SC-004**: Dataset-variable fit is measured against the pass/fail result of FR-006 validation (See US-1)

## Assumptions

- The OpenNeuro datasets (ds000246, ds003474) contain both EEG recordings with frontal/parietal electrode coverage AND behavioral performance measures (k-scores or d') needed to compute working memory capacity
- Findings will be framed as associational rather than causal, as this is an observational study without random assignment to conditions
- Sample size will be sufficient for correlation analyses with power ≥0.80; if the available dataset yields N<30, the pipeline MUST halt and flag 'INSUFFICIENT POWER: N < 30. Redesign required (e.g., data aggregation or power analysis)' rather than proceeding with acknowledged limitation
- MNE-Python preprocessing will run within the GitHub Actions free-tier limit; if preprocessing exceeds this, the dataset will be sampled to reduce trial count while maintaining ≥20 trials per condition
- Alpha power and PLV may exhibit collinearity (both derive from the same EEG signal); the analysis will report joint relationships descriptively and include a variance inflation factor (VIF) diagnostic to assess multicollinearity (See FR-009)
- No GPU/CUDA is required; all computations (filtering, ICA, Hilbert transform, correlation) are CPU-tractable and will execute on the GitHub Actions free runner with limited CPU and memory resources