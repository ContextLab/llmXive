# Feature Specification: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Feature Branch**: `001-temporal-prediction-errors`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) (US-1)

**Description**: As a researcher, I need to download a publicly available EEG dataset (OpenNeuro **ds001734**, which contains both simple oddball and complex auditory scene conditions), apply standard preprocessing (bandpass filtering 1–40 Hz, ICA artifact rejection, average mastoid re-referencing), and segment the data into epochs around auditory stimuli so that I have a clean, analysis‑ready dataset.

**Why this priority**: Without clean, segmented data, no statistical analysis can be performed. This is the foundational step for the entire project.

**Independent Test**: Can be fully tested by running the preprocessing script on a subset of the ds001734 dataset and verifying that the output contains valid epoch objects with a time window of –200 ms to 500 ms and no NaN values in the signal channels (verified via `np.isnan(epochs.get_data()).any()` returning `False`). This is a hard stop condition; if NaNs are present, the pipeline must halt.

**Acceptance Scenarios**:
1. **Given** a valid OpenNeuro dataset ID (ds001734), **When** the download and preprocessing script is executed, **Then** a MNE‑Python `Epochs` object is created with a sampling rate matching the source and a time window spanning a pre‑stimulus interval to 500 ms post‑stimulus.
2. **Given** raw EEG data containing ocular artifacts, **When** ICA is applied with a standard threshold (explaining > 99 % variance), **Then** the identified artifact components are rejected, and the reconstructed signal shows reduced blink/eye‑movement contamination.

---

### User Story 2 - MMN Quantification and Complexity Comparison (Priority: P2) (US-2)

**Description**: As a researcher, I need to compute the Mismatch Negativity (MMN) metrics (amplitude, latency, topography) for both simple oddball and complex auditory scene conditions from the ds001734 dataset, and statistically compare them to determine if prediction‑error signatures scale with scene complexity.

**Why this priority**: This is the core scientific contribution of the project, directly addressing the research question.

**Independent Test**: Can be fully tested by running the analysis script on a subset of the ds001734 dataset (specifically the 'simple' and 'complex' conditions) and verifying that the script correctly identifies the amplitude/latency differences and outputs the statistical test results (t‑values, p‑values, effect sizes).

**Acceptance Scenarios**:
1. **Given** preprocessed epochs for simple and complex conditions from ds001734, **When** the MMN quantification script is run, **Then** it outputs a table of mean amplitude differences (deviant minus standard) in the early post‑stimulus window for fronto‑central electrodes.
2. **Given** the computed MMN metrics for both conditions, **When** the statistical comparison is performed, **Then** the script outputs paired t‑test results with FDR‑corrected p‑values and effect sizes (Cohen's d).

---

### User Story 3 - Visualization and Reporting (Priority: P3) (US-3)

**Description**: As a researcher, I need to generate publication‑quality visualizations (ERP waveforms, scalp topography maps, significance plots) and a summary report so that I can interpret the results and share them with the community.

**Why this priority**: Visualization is essential for interpreting complex EEG data and communicating findings, but it is secondary to the statistical analysis itself.

**Independent Test**: Can be fully tested by running the visualization script and verifying that it generates PNG/SVG files for the ERP waveforms and topographic maps without errors.

**Acceptance Scenarios**:
1. **Given** the statistical results from User Story 2, **When** the visualization script is executed, **Then** it generates an ERP plot showing waveforms for standard and deviant trials across complexity conditions with the MMN window highlighted.
2. **Given** the topographic data, **When** the script is executed, **Then** it generates scalp maps for the early post‑stimulus window showing the spatial distribution of the MMN for both conditions.

---

### Terminology Note

The identifiers “User Story X” and the shorthand “(US‑X)” used throughout the specification refer to the same story and are interchangeable.

### Edge Cases

- What happens if the dataset metadata does not clearly distinguish between "simple" and "complex" auditory scenes? (Handled by explicit metadata validation; if ambiguous, the system logs a warning and halts, as heuristic fallbacks are scientifically invalid for this research question).
- How does the system handle subjects with excessive artifacts (>50 % rejected epochs)? (The system excludes these subjects from the final analysis and logs the exclusion count).
- How does the system handle missing channels in the EEG cap? (The system interpolates missing channels using spherical splines before averaging, provided <10 % are missing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache the OpenNeuro ds001734 dataset using `wget` or `curl` and verify file integrity via checksums. (See US-1)
- **FR-002**: System MUST preprocess raw EEG data by applying a bandpass filter (1–40 Hz), performing ICA for artifact rejection, and re-referencing to average mastoids. (See US-1)
- **FR-003**: System MUST segment continuous data into epochs (‑200 ms to 500 ms) relative to stimulus onsets and classify them as "simple" or "complex" based on the `condition_label` column in `events.tsv` from ds001734. (See US-1)
- **FR-004**: System MUST compute MMN amplitude (mean voltage difference in 150–250 ms window) and latency (peak difference time) for fronto‑central electrodes for both conditions. (See US-2)
- **FR-005**: System MUST perform paired t‑tests comparing MMN metrics between conditions and apply FDR correction for multiple comparisons across electrodes. (See US-2)
- **FR-006**: System MUST generate visualizations including ERP waveforms, scalp topography maps, and statistical significance plots. (See US-3)
- **FR-008**: System MUST verify that the dataset contains both 'simple' and 'complex' conditions. If the 'complex' condition is missing, the system MUST halt and report "Dataset lacks required 'complex' condition; research question untestable with current data." (See US-2) **[Justification: essential to answer the core hypothesis about complexity scaling]**
- **FR-009**: System MUST generate a 'canonical MMN topography template' by averaging the MMN topography (deviant minus standard) across all participants in the 'simple' condition of ds001734 and saving it to `data/templates/canonical_mmn.npy`. This template is required for assessing topographic consistency. (See US-2) **[Justification: provides a reproducible reference for cross‑subject topographic comparison]**
- **FR-010**: System MUST retrieve established literature benchmarks for MMN effect sizes (Cohen's d ≥ 0.5 for a medium effect) from `data/benchmarks/mmn_effect_sizes.json` and compare the calculated Cohen's d against this threshold to determine practical significance. (See US-2) **[Justification: contextualises observed effects against field standards]**
- **FR-011**: System MUST calculate the 'noise floor' as the standard deviation of the pre‑stimulus baseline (‑200 ms to 0 ms) and validate that the MMN amplitude difference exceeds this noise floor by a factor of ≥ 3.0 (Signal‑to‑Noise Ratio ≥ 3.0) to ensure signal validity. (See US-1) **[Justification: standard EEG quality‑control criterion (see e.g., Luck 2014)]**
- **FR-012**: System MUST execute the Reference‑Validator Agent at three specific points: (1) before dataset download to verify the dataset ID and URL against primary sources, (2) before analysis to verify the presence of required conditions, and (3) before reporting to verify all citations. (See US-1, US-2)
- **FR-013**: System MUST record artifact hashes and versioning information explicitly in `state/projects/PROJ-250-neural-correlates-of-temporal-prediction.yaml` to ensure compliance with Constitution Principle V. (See US-1)
- **FR-014**: System MUST validate all data and output against the specific schema files defined in `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` using `pytest` contract tests. (See US-3)
- **FR-015**: System MUST aggregate the 'Statistical Result' entity into the 'MMN Metric' output structure as defined in `contracts/output.schema.yaml`, ensuring traceability between the data model and the output schema. This supports reproducible reporting and downstream meta‑analysis. (See US-2) **[Justification: guarantees that statistical outcomes are embedded in the primary MMNMetric record for reproducibility]**
- **FR-016**: System MUST perform an a priori power analysis for a paired t‑test to detect an effect size d = 0.5 with 80 % power (α = 0.05). If, after subject exclusion, the remaining sample size N falls below the required threshold, the pipeline MUST abort the confirmatory analysis and flag the result as exploratory. (See US-2)

### Key Entities

- **EEG Dataset**: Represents the raw and processed neurophysiological data, including channels, time points, and events.
- **Epoch**: A segment of EEG data centered on a stimulus event, labeled by condition (simple/complex) and type (standard/deviant).

## Data Model

- **MMNMetric**  
  - `amplitude`: float (µV) – mean voltage difference in the 150–250 ms window  
  - `latency`: float (ms) – time of peak difference within the window  
  - `window_start`: float (ms) – start of measurement window (default 150)  
  - `window_end`: float (ms) – end of measurement window (default 250)  
  - `topography`: array[float] – electrode‑wise differences (deviant − standard)  
  - `benchmark_reference`: string – identifier of literature benchmark used (e.g., "mmn_effect_sizes_v1")  

- **StatisticalResult**  
  - `test_name`: string (e.g., "paired_t")  
  - `t_value`: float  
  - `p_value`: float (FDR‑corrected)  
  - `effect_size`: float (Cohen's d)  
  - `power_analysis_required_n`: integer (from FR‑016)  

## Success Criteria *(mandatory)*

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: MMN amplitude difference (deviant vs. standard) is measured against the baseline noise floor (pre‑stimulus SD) to ensure signal validity (SNR ≥ 3.0). (See US-1)
- **SC-002**: Statistical significance (p‑value) of MMN differences between complexity conditions is measured against the FDR‑corrected alpha threshold (0.05). (See US-2)
- **SC-003**: Effect size (Cohen's d) of the complexity effect is measured against established benchmarks for MMN effect sizes in literature (d ≥ 0.5) to quantify practical significance. (See US-2)
- **SC-004**: Topographic consistency of the MMN across participants is measured against the 'canonical MMN topography template' generated from the 'simple' condition of ds001734 using Pearson correlation coefficient (r ≥ 0.8). (See US-2)
- **SC-005**: Visualization scripts generate PNG/SVG files for ERP waveforms and topographic maps without errors; file existence and non‑empty size are verified. (See US-3)
- **SC-006**: Power analysis requirement satisfied: post‑exclusion sample size N ≥ required N; otherwise the analysis is flagged as exploratory and the pipeline aborts confirmatory testing. (See US-2)
- **SC-007**: Dataset download integrity is confirmed by matching file checksums to published values. (See US-1)
- **SC-008**: Preprocessed epochs contain no NaN values in any channel (asserted via `np.isnan`). (See US-1)
- **SC-009**: Visualization scripts produce non‑empty PNG/SVG files; file sizes > 0 KB and are readable. (See US-3)

## Assumptions

- The OpenNeuro ds001734 dataset contains both simple oddball and complex auditory scene conditions with a `condition_label` column in `events.tsv`.
- The EEG data is recorded with a sufficient number of channels (≥ 32) to allow for accurate topographic mapping of the MMN component.
- The analysis will be performed using MNE‑Python on a CPU‑only environment (GitHub Actions free tier) with ≤ 7 GB RAM and ≤ 6 hours runtime.
- The MMN component will be observable in the early post‑stimulus time window for both conditions, consistent with established literature.
- The dataset contains no more than 20 % of subjects with excessive artifacts, ensuring sufficient statistical power after exclusions.
- The Benjamini‑Hochberg FDR correction method is appropriate for the number of electrodes tested and provides adequate control of false positives.
- Heuristic fallbacks for missing 'complex' conditions are scientifically invalid and will not be attempted; the system will halt if the condition is missing.
