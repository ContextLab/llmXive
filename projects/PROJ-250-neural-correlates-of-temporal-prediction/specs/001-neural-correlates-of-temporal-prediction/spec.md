# Feature Specification: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Feature Branch**: `001-temporal-prediction-errors`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

**Description**: As a researcher, I need to download a publicly available EEG dataset (OpenNeuro ds004510, which contains both simple oddball and complex auditory scene conditions), apply standard preprocessing (bandpass filtering 1–40 Hz, ICA artifact rejection, average mastoid re-referencing), and segment the data into epochs around auditory stimuli so that I have a clean, analysis-ready dataset.

**Why this priority**: Without clean, segmented data, no statistical analysis can be performed. This is the foundational step for the entire project.

**Independent Test**: Can be fully tested by running the preprocessing script on a subset of the ds004510 dataset and verifying that the output contains valid epoch objects with correct time windows (-200 to 500ms) and no NaN values in the signal channels (verified via `np.isnan(epochs.get_data()).any()` returning `False`). This is a hard stop condition; if NaNs are present, the pipeline must halt.

**Acceptance Scenarios**:
1. **Given** a valid OpenNeuro dataset ID (ds004510), **When** the download and preprocessing script is executed, **Then** a MNE-Python `Epochs` object is created with a sampling rate matching the source and a time window of -200ms to 500ms.
2. **Given** raw EEG data containing ocular artifacts, **When** ICA is applied with a standard threshold (e.g., explaining >99% variance), **Then** the identified artifact components are rejected, and the reconstructed signal shows reduced blink/eye-movement contamination.

---

### User Story 2 - MMN Quantification and Complexity Comparison (Priority: P2)

**Description**: As a researcher, I need to compute the Mismatch Negativity (MMN) metrics (amplitude, latency, topography) for both simple oddball and complex auditory scene conditions from the ds004510 dataset, and statistically compare them to determine if prediction error signatures scale with scene complexity.

**Why this priority**: This is the core scientific contribution of the project, directly addressing the research question.

**Independent Test**: Can be fully tested by running the analysis script on a subset of the ds004510 dataset (specifically the 'simple' and 'complex' conditions) and verifying that the script correctly identifies the amplitude/latency differences and outputs the statistical test results (t-values, p-values, effect sizes).

**Acceptance Scenarios**:
1. **Given** preprocessed epochs for simple and complex conditions from ds004510, **When** the MMN quantification script is run, **Then** it outputs a table of mean amplitude differences (deviant minus standard) in the 150–250ms window for fronto-central electrodes.
2. **Given** the computed MMN metrics for both conditions, **When** the statistical comparison is performed, **Then** the script outputs paired t-test results with FDR-corrected p-values and effect sizes (Cohen's d).

---

### User Story 3 - Visualization and Reporting (Priority: P3)

**Description**: As a researcher, I need to generate publication-quality visualizations (ERP waveforms, scalp topography maps, significance plots) and a summary report so that I can interpret the results and share them with the community.

**Why this priority**: Visualization is essential for interpreting complex EEG data and communicating findings, but it is secondary to the statistical analysis itself.

**Independent Test**: Can be fully tested by running the visualization script and verifying that it generates PNG/SVG files for the ERP waveforms and topographic maps without errors.

**Acceptance Scenarios**:
1. **Given** the statistical results from User Story 2, **When** the visualization script is executed, **Then** it generates an ERP plot showing waveforms for standard and deviant trials across complexity conditions with the MMN window highlighted.
2. **Given** the topographic data, **When** the script is executed, **Then** it generates scalp maps for the 150–250ms window showing the spatial distribution of the MMN for both conditions.

---

### Edge Cases

- What happens if the dataset metadata does not clearly distinguish between "simple" and "complex" auditory scenes? (Handled by requiring explicit metadata validation; if ambiguous, the system logs a warning and halts the process, as heuristic fallbacks are scientifically invalid for this research question).
- How does the system handle subjects with excessive artifacts (>50% rejected epochs)? (The system excludes these subjects from the final analysis and logs the exclusion count).
- How does the system handle missing channels in the EEG cap? (The system interpolates missing channels using spherical splines before averaging, provided <10% are missing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache the OpenNeuro ds004510 dataset using `wget` or `curl` and verify file integrity via checksums. (See US-1)
- **FR-002**: System MUST preprocess raw EEG data by applying a bandpass filter (1–40 Hz), performing ICA for artifact rejection, and re-referencing to average mastoids. (See US-1)
- **FR-003**: System MUST segment continuous data into epochs (-200ms to 500ms) relative to stimulus onsets and classify them as "simple" or "complex" based on the `condition_label` metadata in `events.tsv` from ds004510. (See US-1)
- **FR-004**: System MUST compute MMN amplitude (mean voltage difference in 150–250ms window) and latency (peak difference time) for fronto-central electrodes for both conditions. (See US-2)
- **FR-005**: System MUST perform paired t-tests comparing MMN metrics between conditions and apply FDR correction for multiple comparisons across electrodes. (See US-2)
- **FR-006**: System MUST generate visualizations including ERP waveforms, scalp topography maps, and statistical significance plots. (See US-3)
- **FR-008**: System MUST verify that the dataset contains both 'simple' and 'complex' conditions. If the 'complex' condition is missing, the system MUST halt and report "Dataset lacks required 'complex' condition; research question untestable with current data." (See US-2)
- **FR-009**: System MUST generate a 'canonical MMN topography template' by averaging the MMN topography (deviant minus standard) across all participants in the 'simple' condition of the ds004510 dataset and saving it to `data/templates/canonical_mmn.npy`. (See SC-004)
- **FR-010**: System MUST retrieve established literature benchmarks for MMN effect sizes (specifically Cohen's d ≥ 0.5 for medium effect) from a predefined source (e.g., `data/benchmarks/mmn_effect_sizes.json`) and compare the calculated Cohen's d against this threshold to determine 'practical significance'. (See SC-003)
- **FR-011**: System MUST calculate the 'noise floor' as the standard deviation of the pre-stimulus baseline (-200ms to 0ms) and validate that the MMN amplitude difference exceeds this noise floor by a factor of ≥ 3.0 (Signal-to-Noise Ratio ≥ 3.0) to ensure signal validity. (See SC-001)
- **FR-012**: System MUST execute the Reference-Validator Agent at three specific points: (1) before dataset download to verify the dataset ID and URL against primary sources, (2) before analysis to verify the presence of required conditions, and (3) before reporting to verify all citations. (See Constitution Principle II)
- **FR-013**: System MUST record artifact hashes and versioning information explicitly in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` to ensure compliance with Constitution Principle V. (See Constitution Principle V)
- **FR-014**: System MUST validate all data and output against the specific schema files defined in `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` using `pytest` contract tests. (See Technical Context)
- **FR-015**: System MUST aggregate the 'Statistical Result' entity into the 'MMN Metric' output structure as defined in `contracts/output.schema.yaml`, ensuring traceability between the data model and the output schema. (See Data Model)

### Key Entities

- **EEG Dataset**: Represents the raw and processed neurophysiological data, including channels, time points, and events.
- **Epoch**: A segment of EEG data centered on a stimulus event, labeled by condition (simple/complex) and type (standard/deviant).
- **MMN Metric**: A derived data point representing the amplitude or latency of the mismatch negativity component.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: MMN amplitude difference (deviant vs. standard) is measured against the baseline noise floor (pre-stimulus SD) to ensure signal validity (SNR ≥ 3.0). (See FR-011)
- **SC-002**: Statistical significance (p-value) of MMN differences between complexity conditions is measured against the FDR-corrected alpha threshold (0.05). (See FR-005)
- **SC-003**: Effect size (Cohen's d) of the complexity effect is measured against established benchmarks for MMN effect sizes in literature (d ≥ 0.5) to quantify practical significance. (See FR-010)
- **SC-004**: Topographic consistency of the MMN across participants is measured against the 'canonical MMN topography template' generated from the 'simple' condition of ds004510 using Pearson correlation coefficient (r ≥ 0.8). (See FR-009)

## Assumptions

- The OpenNeuro ds004510 dataset contains both simple oddball and complex auditory scene conditions.
- The EEG data is recorded with a sufficient number of channels (≥32) to allow for accurate topographic mapping of the MMN component.
- The analysis will be performed using MNE-Python on a CPU-only environment (GitHub Actions free tier) with ≤7 GB RAM and ≤6 hours runtime.
- The MMN component will be observable in the 150–250ms time window for both conditions, consistent with established literature.
- The dataset contains no more than 20% of subjects with excessive artifacts that would require exclusion, ensuring sufficient statistical power.
- The FDR correction method (Benjamini-Hochberg) is appropriate for the number of electrodes tested and provides adequate control of false positives.
- Heuristic fallbacks for missing 'complex' conditions are scientifically invalid and will not be attempted; the system will halt if the condition is missing.