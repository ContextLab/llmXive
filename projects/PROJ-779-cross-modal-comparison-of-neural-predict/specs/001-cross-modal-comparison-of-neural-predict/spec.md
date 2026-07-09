# Feature Specification: Cross-Modal Comparison of Neural Prediction Error Signals

**Feature Branch**: `001-cross-modal-prediction-error`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: "Cross-Modal Comparison of Neural Prediction Error Signals"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download open EEG/MEG datasets containing auditory and visual oddball paradigms from distinct sources, apply a standardized preprocessing pipeline (bandpass filtering, ICA artifact removal, re-referencing), and verify the data integrity before analysis.

**Why this priority**: Without clean, comparable data from both modalities, no statistical comparison of prediction error signals is possible. This is the foundational step that enables all subsequent analysis.

**Independent Test**: Can be fully tested by running the preprocessing script on a sample dataset and verifying that the output contains cleaned EEG/MEG signals with artifact rejection logs and that the data fits within the 7 GB RAM constraint.

**Acceptance Scenarios**:

1. **Given** an OpenNeuro dataset ID (e.g., ds000246), **When** the preprocessing pipeline is executed, **Then** the system MUST output bandpass-filtered (0.5–40 Hz) and ICA-corrected EEG/MEG data with a log confirming successful artifact removal.
2. **Given** a dataset with ≥100 oddball and ≥300 standard trials, **When** the pipeline processes the data, **Then** the system MUST retain all trials meeting the minimum count threshold and reject trials with excessive artifacts, reporting the rejection rate.
3. **Given** a dataset with sampling rate <500 Hz, **When** the pipeline attempts processing, **Then** the system MUST halt immediately and report a validation error indicating insufficient temporal resolution for MMN/vMMN detection.

---

### User Story 2 - Prediction Error Signal Extraction and Quantification (Priority: P2)

The researcher MUST be able to compute difference waves (oddball − standard) for each modality, extract peak latency and mean amplitude within modality-specific canonical time windows, and generate summary statistics for cross-modal comparison.

**Why this priority**: This transforms raw neural data into quantifiable metrics (latency, amplitude) that directly address the research question about modality-specific differences.

**Independent Test**: Can be fully tested by processing a single modality's data and verifying that the output includes peak latency (in ms), mean amplitude (in µV), and topographic maps for the specified time windows.

**Acceptance Scenarios**:

1. **Given** preprocessed auditory oddball and standard trials, **When** the difference wave is computed at fronto-central electrodes, **Then** the system MUST extract the peak latency within the 100–250 ms window and report the mean amplitude in the same window.
2. **Given** preprocessed visual oddball and standard trials, **When** the difference wave is computed at occipito-parietal electrodes, **Then** the system MUST extract the peak latency within the 150–350 ms window and report the mean amplitude in the same window.
3. **Given** both auditory and visual difference waves, **When** the system generates a summary table, **Then** it MUST include latency and amplitude values for both modalities with clear modality labels.

---

### User Story 3 - Source Localization, Statistical Comparison, and Infrastructure Validation (Priority: P3)

The researcher MUST be able to apply minimum-norm estimation (MNE) to localize prediction error generators, compare source strength across modalities at primary sensory cortical regions, perform statistical tests (independent samples t-tests or permutation tests) with multiple-comparison correction, and validate the entire pipeline end-to-end on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ≤6 h runtime) without GPU acceleration.

**Why this priority**: This addresses the core theoretical question about domain-general vs. modality-specific mechanisms by comparing cortical sources and providing statistical rigor, while ensuring the analysis is computationally feasible for the target environment.

**Independent Test**: Can be fully tested by running the source localization and statistical comparison on a subset of data and verifying that the output includes source strength maps, p-values with Benjamini-Hochberg correction, a statistical decision (reject/fail to reject), and a successful GitHub Actions run within 6 hours.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG/MEG data and a standard head model (ICBM152), **When** minimum-norm estimation is applied using sensor-specific lead fields, **Then** the system MUST generate source strength maps for both auditory and visual prediction error signals.
2. **Given** source strength values at primary sensory cortical regions for both modalities, **When** an independent samples t-test or permutation test (10,000 permutations) is performed, **Then** the system MUST report p-values corrected for multiple comparisons using the Benjamini-Hochberg method and a clear statistical decision (reject/fail to reject null).
3. **Given** the statistical comparison results, **When** the system generates the final report, **Then** it MUST explicitly state whether the cortical generators overlap (supporting domain-general mechanisms) or are distinct (supporting modality-specific mechanisms) based on the defined success criteria.
4. **Given** the full analysis pipeline, **When** executed on a GitHub Actions free-tier runner (2 CPU, 7GB RAM), **Then** the system MUST complete successfully (exit code 0) within 6 hours.

---

### Edge Cases

- **Insufficient Trials**: If a dataset has <100 oddball trials, the system MUST halt and report an error (See FR-008).
- **Missing Modalities**: If a required modality (auditory or visual) is missing from the provided dataset pair, the system MUST halt and report an error (See FR-009).
- **Source Localization Failure**: If MNE fails due to poor SNR or head model mismatch, the system MUST report the failure and skip source analysis for that modality (See FR-010).
- **Sampling Rate Threshold**: If the sampling rate is exactly 500 Hz, the system MUST proceed; if <500 Hz, it MUST halt (See FR-002, FR-011).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and validate two distinct OpenNeuro datasets (one containing an auditory oddball paradigm, one containing a visual oddball paradigm), ensuring ≥100 oddball and ≥300 standard trials per modality (See US-1)
- **FR-002**: System MUST apply a standardized preprocessing pipeline including bandpass filtering (0.5–40 Hz), ICA artifact removal, and common average re-referencing; if sampling rate <500 Hz, the system MUST halt and report an error (See US-1)
- **FR-003**: System MUST compute difference waves (oddball − standard) for each modality at specified electrode regions (fronto-central for auditory, occipito-parietal for visual) (See US-2)
- **FR-004**: System MUST extract peak latency and mean amplitude from difference waves within modality-specific windows (100–250 ms for auditory, 150–350 ms for visual) (See US-2)
- **FR-005**: System MUST apply minimum-norm estimation (MNE) using sensor-specific lead fields and the ICBM152 head model to localize prediction error generators in primary sensory cortical regions (Heschl's gyrus for auditory, Calcarine/Fusiform for visual) (See US-3)
- **FR-006**: System MUST perform statistical comparison of latency, amplitude, and source strength across modalities using independent samples t-tests or non-parametric permutation tests (10,000 permutations) with Benjamini-Hochberg correction; the system MUST report the p-value and the statistical decision (reject/fail to reject null) (See US-3)
- **FR-007**: System MUST validate the analysis pipeline end-to-end on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ≤6 h runtime) without GPU acceleration, completing with exit code 0 within 6 hours (See US-3)
- **FR-008**: System MUST halt and report a specific error if the number of oddball trials is <100 (See Edge Cases)
- **FR-009**: System MUST halt and report a specific error if the required auditory or visual modality is missing from the dataset pair (See Edge Cases)
- **FR-010**: System MUST report a failure and skip source analysis if MNE fails due to low SNR or head model mismatch (See Edge Cases)
- **FR-011**: System MUST validate the sampling rate is ≥500 Hz before processing; if <500 Hz, it MUST halt (See Edge Cases)
- **FR-012**: System MUST include source strength in the statistical comparison of cross-modal differences (See US-3)
- **FR-013**: System MUST perform a split-half reliability analysis (Cronbach's α ≥ 0.7) on the extracted prediction error metrics to validate internal consistency, serving as the independence check in lieu of behavioral data (See US-3)
- **FR-014**: System MUST perform a sensitivity analysis on the source localization by sweeping the spatial smoothing kernel (σ ∈ {5, 10, 15} mm) and report the variation in source strength to quantify localization uncertainty (See US-3)

### Key Entities

- **NeuralSignal**: Represents preprocessed EEG/MEG data with attributes including sampling rate, number of trials, electrode locations, and artifact rejection status
- **PredictionErrorMetric**: Represents quantified prediction error signals with attributes including peak latency (ms), mean amplitude (µV), and time window (100–250 ms auditory, 150–350 ms visual)
- **CorticalSource**: Represents localized prediction error generators with attributes including brain region (e.g., Heschl's gyrus, Calcarine), source strength, and spatial coordinates
- **HomologousRegion**: Defines the primary sensory cortical regions used for comparison (Auditory: Heschl's gyrus; Visual: Calcarine/Fusiform)

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Prediction error signal latency difference between auditory and visual modalities is measured against a literature-derived threshold of |Δt| < 50ms for 'domain-general' classification (See US-2)
- **SC-002**: Cortical source overlap is measured against two mutually exclusive success conditions: (A) Overlap score > 0.6 AND p > 0.05 (supports domain-general) OR (B) Overlap score ≤ 0.6 AND p ≤ 0.05 (supports modality-specific) (See US-3)
- **SC-003**: Statistical significance of cross-modal differences is measured against the Benjamini-Hochberg corrected p-value threshold (α = 0.05) (See US-3)
- **SC-004**: Computational feasibility is measured against the GitHub Actions free-tier constraints (2 CPU cores, ~7 GB RAM, ≤6 h runtime, exit code 0) (See US-3)
- **SC-005**: Validation Independence is measured against a split-half reliability threshold of Cronbach's α ≥ 0.7 (See US-3)

## Assumptions

- OpenNeuro datasets representing auditory and visual modalities are used as representative examples of valid datasets.; the pipeline is designed to support any two distinct datasets meeting the trial count and sampling rate criteria.
- The ICBM152 head model provides adequate anatomical accuracy for source localization of prediction error signals in both auditory and visual modalities, though spatial uncertainty is acknowledged and quantified via FR-014.
- Benjamini-Hochberg correction is appropriate for controlling false discovery rate across the multiple comparisons of electrodes and time windows.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) can execute the entire preprocessing, analysis, and statistical comparison pipeline within the 6-hour runtime limit.
- The prediction error signals (MMN and vMMN) can be reliably extracted using the specified modality-specific time windows for both auditory and visual modalities.
- Behavioral measures (reaction time, accuracy) are NOT used for cross-validation as passive oddball paradigms often lack valid behavioral correlates; internal split-half reliability (FR-013) is used instead to satisfy the Validation Independence principle.