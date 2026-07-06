# Feature Specification: Exploring the Relationship Between Brain Network Dynamics and Individual Differences in Dream Recall Frequency

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Do individual differences in resting-state dynamic functional connectivity (specifically network flexibility and stability) predict self-reported dream recall frequency?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST automatically download resting-state fMRI data from OpenNeuro dataset ds000228, perform standard denoising (ICA-AROMA) and normalization, and ensure intermediate files remain under 7 GB RAM to fit the CI runner constraints.

**Why this priority**: Without a clean, memory-safe dataset, no analysis can occur. This is the foundational step that enables all subsequent metric extraction and statistical testing.

**Independent Test**: Can be fully tested by executing the download and preprocessing script on a subset of 5 subjects and verifying the output files exist, are < 7 GB, and contain the required metadata fields.

**Acceptance Scenarios**:
1. **Given** the OpenNeuro dataset ds000228, **When** the preprocessing script runs, **Then** the output NIfTI files are normalized and denoised, the total directory size is ≤ 7 GB, and the peak memory usage log entry is < 7GB.
2. **Given** a study with > 50 subjects, **When** the script runs with a target N=50 limit, **Then** exactly 50 subjects are processed and the rest are skipped with a log entry.
3. **Given** a corrupted download, **When** the script runs, **Then** the process fails gracefully with a specific error message and does not produce partial, misleading output files.

---

### User Story 2 - Dynamic Connectivity Metric Extraction (Priority: P2)

The system MUST calculate network flexibility and stability metrics for the Default Mode Network (DMN), Salience, and Hippocampal networks using the Schaefer-400 parcellation atlas. The process MUST cluster time-varying connectivity matrices into discrete states using the Louvain algorithm before calculating the number of state transitions per unit time.

**Why this priority**: This transforms raw imaging data into the specific predictor variables (flexibility/stability) required to answer the research question. The clustering step is mathematically mandatory for defining network states.

**Independent Test**: Can be fully tested by running the metric extraction on a single preprocessed subject and verifying that the output CSV contains the calculated flexibility and stability values for the specified networks.

**Acceptance Scenarios**:
1. **Given** a preprocessed 4D fMRI file and the Schaefer-400 atlas, **When** the sliding window correlation runs, **Then** a time-varying connectivity matrix is generated for each window.
2. **Given** a time-varying connectivity matrix, **When** the Louvain clustering is applied, **Then** a sequence of discrete community partitions is generated.
3. **Given** the discrete partitions, **When** the flexibility metric is calculated, **Then** the output is a single float value representing the number of state transitions per unit time for the DMN, Salience, and Hippocampal networks.
4. **Given** missing metadata for dream recall frequency, **When** the extraction runs, **Then** the subject is excluded from the final analysis dataset with a warning logged.

---

### User Story 3 - Statistical Analysis and Visualization (Priority: P3)

The system MUST perform Spearman correlation between network metrics and dream recall frequency, apply FDR correction for multiple comparisons, and run 1000 iterations of permutation testing to establish null distributions.

**Why this priority**: This delivers the final scientific result (correlation strength, p-value) and validates the finding against the null hypothesis, completing the research loop.

**Independent Test**: Can be fully tested by running the analysis on the extracted metrics and verifying the output includes a correlation coefficient, a corrected p-value, and a histogram of the permutation null distribution.

**Acceptance Scenarios**:
1. **Given** a dataset of 50 subjects with metrics and dream recall frequency values, **When** the correlation analysis runs, **Then** a Spearman correlation coefficient (rho) and uncorrected p-value are calculated.
2. **Given** multiple network metrics tested, **When** FDR correction is applied, **Then** the output includes adjusted p-values for each tested relationship.
3. **Given** the primary correlation result, **When** 1000 permutation iterations are run, **Then** the empirical p-value is derived and reported if it differs significantly from the parametric result.

### Edge Cases

- What happens when the OpenNeuro study metadata does not contain a "dream recall frequency" field? The system must log a specific "Missing Metadata" error and skip the study rather than crashing.
- How does the system handle subjects with motion artifacts exceeding a threshold (e.g., FD > 0.5mm)? The system must exclude these subjects from the final N count and report the exclusion rate.
- How does the system handle a null result (p > 0.05)? The system must still generate the full report including the null distribution plot and the specific correlation coefficient, rather than suppressing output.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data from OpenNeuro dataset ds000228 and filter for studies containing the "dream recall frequency" field (See US-1).
- **FR-002**: System MUST perform ICA-AROMA denoising and spatial normalization while monitoring peak RSS via /proc/self/status and failing the job if it exceeds 7 GB RAM (See US-1).
- **FR-003**: System MUST implement a sliding window correlation method with a fixed window size of 30 seconds and a step size of 10 seconds, followed by Louvain clustering to generate discrete community partitions (See US-2).
- **FR-004**: System MUST calculate network flexibility and stability metrics specifically for the DMN, Salience, and Hippocampal-Memory networks using the Schaefer-400 parcellation atlas and NetworkX (See US-2).
- **FR-005**: System MUST perform Spearman correlation analysis between the extracted network metrics and self-reported dream recall frequency values (See US-3).
- **FR-006**: System MUST apply False Discovery Rate (FDR) correction to all correlation p-values to account for multiple hypothesis testing (See US-3).
- **FR-007**: System MUST execute a permutation test with exactly 1000 iterations to generate a null distribution for the primary correlation hypothesis (See US-3).
- **FR-008**: System MUST output results in a machine-readable format (JSON/CSV) containing the correlation coefficient, FDR-corrected p-value, and permutation p-value (See US-3).
- **FR-009**: System MUST perform a post-hoc power analysis to estimate the detectable effect size given the N=50 sample size and report the result (See US-3).

### Key Entities

- **Subject**: An individual participant represented by their fMRI scan ID, dream recall frequency value, and demographic metadata.
- **Connectivity Matrix**: A time-varying representation of functional connectivity between brain regions derived from sliding window analysis.
- **Network Metric**: A quantitative value (flexibility or stability) derived from a specific brain network (DMN, Salience, Hippocampal-Memory) for a single subject.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between DMN flexibility and dream recall frequency is measured against the null hypothesis of no association, with a post-hoc power analysis reported to validate the study's sensitivity (See US-3, FR-005, FR-009).
- **SC-002**: The family-wise error rate is measured against the FDR-corrected threshold (q < 0.05) to control for multiple comparisons across networks (See US-3, FR-006).
- **SC-003**: The robustness of the observed correlation is measured against the empirical null distribution generated by 1000 permutation iterations (See US-3, FR-007).
- **SC-004**: The peak memory usage of the preprocessing pipeline is measured against the 7 GB RAM constraint of the CI runner (See US-1, FR-002).
- **SC-005**: The computational runtime of the full analysis pipeline is measured against the 6-hour job limit, with a target of ≤4 hours to allow for retries (See Assumptions, US-1).

## Assumptions

- The OpenNeuro dataset ds000228 contains a validated questionnaire field for "dream recall frequency" that can be mapped to a continuous or ordinal scale.
- The resting-state fMRI data is of sufficient quality (TR ≤ 2s) to support the 30-second sliding window analysis without excessive noise.
- The "dream recall frequency" variable is treated as a continuous or ordinal scale; if it is strictly binary, the analysis will default to a point-biserial correlation or logistic regression as a sensitivity check.
- The 50-subject sample size provides sufficient statistical power to detect a medium effect size (r = 0.3) at alpha = 0.05, acknowledging this is a power-limited study; a post-hoc power analysis (FR-009) will quantify this limitation.
- The analysis assumes that resting-state dynamics are stable enough within a single session to be predictive of trait-like dream recall frequency.
- No GPU acceleration is available; all computations (Nilearn, NetworkX, Scipy) must run on CPU-only logic within the 6-hour window.