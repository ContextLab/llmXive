# Feature Specification: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Feature Branch**: `001-neural-correlates-of-simulated-social-ex`  
**Created**: 2026-10-14  
**Status**: Draft  
**Input**: User description: "How does acute simulated social exclusion modulate functional connectivity dynamics within the default mode network (DMN)?"

## User Scenarios & Testing

### User Story 1 – Data Ingestion & Quality Control (US-1)

The system must download preprocessed fMRI data from OpenNeuro (e.g., the Cyberball task dataset `ds000030`), verify that the metadata contains distinct “Inclusion” and “Exclusion” event markers, extract raw BOLD time‑series from the canonical DMN regions (PCC, mPFC, left/right angular gyrus) using the Harvard‑Oxford atlas, compute framewise displacement for each run, and exclude any subject whose **mean** displacement exceeds **0.2 mm**.

**Why this priority**: Clean, correctly annotated data are a prerequisite for any downstream analysis; without them the scientific question cannot be answered.

**Independent Test**: Execute the ingestion pipeline on a single subject file and check that (a) motion metrics are produced, (b) event markers are detected, (c) ROI time‑series are extracted, and (d) the subject is either retained or excluded according to the 0.2 mm rule.

**Acceptance Scenarios**  

1. **Given** a preprocessed NIfTI file with valid event markers, **when** the motion‑assessment module runs, **then** the system outputs a mean displacement value and **retains** the subject if the value ≤ 0.2 mm.  
2. **Given** a subject with mean displacement > 0.2 mm, **when** the same module runs, **then** the system flags the subject as **excluded**.  
3. **Given** a dataset missing either “Inclusion” or “Exclusion” markers, **when** the ingestion module runs, **then** the system aborts with error code **101897695** (see FR‑011).

---

### User Story 2 – Connectivity Metric Computation (US-2)

For each retained subject, the system must compute Pearson correlation matrices among the three DMN ROIs **separately** for the Inclusion and Exclusion conditions, then derive a “connectivity strength” metric per condition by **averaging the Pearson correlation values across all ROI pairs (preserving sign)**. The primary outcome is the **difference** (Exclusion – Inclusion) in connectivity strength.  
Additionally, to capture dynamics, the system must perform a sliding‑window (30 s window, 5 s step) correlation analysis, producing a time‑resolved connectivity‑strength series for each condition.

**Why this priority**: This transforms raw BOLD signals into both static and dynamic quantitative variables required to test the hypothesis about DMN modulation.

**Independent Test**: Run the connectivity module on a subject with known event timings and verify that (a) static correlation matrices are generated per condition, (b) the mean correlation metric is calculated correctly for each condition, and (c) the sliding‑window series are produced with the specified parameters.

**Acceptance Scenarios**  

1. **Given** raw time‑series for PCC and mPFC during the Exclusion condition, **when** the correlation module runs, **then** it outputs the Pearson correlation coefficient computed directly from the measured signals.  
2. **Given** a subject with both Inclusion and Exclusion time‑series, **when** the strength calculator runs, **then** it outputs two distinct connectivity‑strength values (one per condition) derived from empirical data.  
3. **Given** the same time‑series, **when** the dynamic analysis runs, **then** it outputs a time‑resolved series of connectivity strengths using a 30 s window stepped every 5 s.

---

### User Story 3 – Statistical Hypothesis Testing (US-3)

The system must perform a **non‑parametric paired permutation test** (10 000 permutations) comparing the per‑subject connectivity‑strength difference between Exclusion and Inclusion. It must report a two‑tailed p‑value, Cohen’s d effect size, and generate (a) a histogram of the null distribution, (b) a bar plot of the observed mean difference with 95 % confidence intervals derived from the permutation distribution, and (c) ROI‑wise correlation‑matrix heatmaps for each condition.

**Why this priority**: This delivers the final scientific answer, quantifying whether DMN connectivity is significantly modulated by social exclusion and providing visual validation.

**Independent Test**: Run the permutation test on the full retained sample and confirm that (a) exactly 10 000 permutations are performed, (b) the p‑value is computed from the empirical null, (c) the required visualizations are produced, and (d) the test module accepts an explicit random‑seed argument.

**Acceptance Scenarios**  

1. **Given** paired connectivity‑strength values for N ≥ 10 subjects, **when** the permutation test runs with 10 000 iterations, **then** the system outputs a p‑value, Cohen’s d, and the full null‑distribution histogram.  
2. **Given** the statistical results, **when** the visualization module runs, **then** it generates (a) a bar plot showing the mean difference with 95 % CI error bars, (b) the null‑distribution histogram, (c) heatmaps of the ROI‑wise correlation matrices for Inclusion and Exclusion, all saved as PNG files in the output directory.

### Edge Cases

- **Insufficient Subjects**: If fewer than **10** subjects remain after QC, the system must halt execution and return error code **101897696** (see FR‑009).  
- **Partial ROI Failure**: If time‑series extraction fails for any required DMN ROI in a subject, that subject is excluded from all downstream analyses (see FR‑014).  
- **Dataset Unavailability**: If the OpenNeuro API is unreachable or the specified dataset is missing, the system retries up to **3** times with exponential backoff (1 s, 2 s, 4 s) before failing with error code **ERR_DATA_UNAVAILABLE** (see FR‑013).  
- **Missing Condition Data**: Subjects lacking either Inclusion or Exclusion event markers are excluded from the paired analysis (see FR‑010).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download preprocessed fMRI data from OpenNeuro (e.g., `ds000030`) and verify file integrity before processing. *(See US‑1)*
- **FR-002**: System MUST compute mean framewise displacement for each subject and exclude any subject with mean displacement > 0.2 mm. *(See US‑1)*
- **FR-003**: System MUST extract raw BOLD time‑series for PCC, mPFC, and left/right angular gyrus using the Harvard‑Oxford cortical atlas. *(See US‑1)*
- **FR-004**: System MUST compute Pearson correlation matrices for the DMN ROIs separately for Inclusion and Exclusion conditions, using the raw time‑series. *(See US‑2)*
- **FR-005**: System MUST calculate a “connectivity strength” metric per condition by averaging the Pearson correlation values across all ROI pairs (preserving sign). The primary outcome is the difference (Exclusion – Inclusion). *(See US‑2)*
- **FR-006**: System MUST perform a non‑parametric paired permutation test with **10 000** iterations on the per‑subject connectivity‑strength differences, reporting a two‑tailed p‑value and Cohen’s d effect size. *(See US‑3)*
- **FR-009**: System MUST halt execution and return error code **101897696** if the number of valid subjects after QC is < 10. *(Edge Cases)*
- **FR-010**: System MUST abort execution and return error code **101897695** if the dataset lacks required “Inclusion” or “Exclusion” event markers. *(See US‑1)*
- **FR-011**: System MUST verify that each retained subject has valid time‑series for **both** Inclusion and Exclusion conditions; subjects missing either condition are excluded from the paired analysis. *(Edge Cases)*
- **FR-013**: System MUST retry the dataset download up to **3** attempts with exponential backoff (1 s → 2 s → 4 s). If all attempts fail, it returns error code `ERR_DATA_UNAVAILABLE`. *(Edge Cases)*
- **FR-014**: System MUST exclude a subject from all downstream analyses if extraction of the raw time‑series fails for **any** required DMN ROI. *(Edge Cases)*
- **FR-015**: System MUST generate (a) a histogram of the permutation‑test null distribution and (b) a bar plot of the mean connectivity‑strength difference with 95 % confidence‑interval error bars, saving both as PNG files in the designated output folder. *(See US‑3)*
- **FR-016**: System MUST allow the permutation‑test module to accept an explicit random‑seed parameter for reproducibility. *(See US‑3)*
- **FR-017**: System MUST generate ROI‑wise correlation‑matrix heatmaps for each condition (Inclusion and Exclusion) and save them as PNG files. *(See US‑3)*
- **FR-018**: System MUST compute dynamic (sliding‑window) functional connectivity using a 30 s window stepped every 5 s, and output time‑resolved connectivity‑strength series for each condition. *(See US‑2)*

### Key Entities

- **Subject** – Represents an individual participant; attributes include subject ID, mean displacement, and inclusion/exclusion condition labels.  
- **TimeSeries** – Raw BOLD signal for a specific ROI, subject, and condition.  
- **ConnectivityMatrix** – Pearson correlation coefficients among all DMN node pairs for a given condition.  
- **Result** – Outcome of the statistical test, containing p‑value, Cohen’s d, and confidence‑interval information.

## Success Criteria

- **SC-001**: The proportion of subjects retained after motion QC is measured against the total number of downloaded subjects; ≥ 80 % retention is expected for a typical Cyberball dataset. *(See FR‑002, US‑1)*
- **SC-002**: Re‑running the permutation test **5** times with different random seeds yields a standard deviation of the resulting p‑values ≤ 0.01, demonstrating stability of the inference. *(See FR‑006, FR‑016, US‑3)*
- **SC-003**: The required visualizations (null‑distribution histogram and bar plot with 95 % CI) exist in the output directory, are correctly labeled, and contain the expected graphical elements (titles, axis labels, confidence‑interval bars). *(See FR‑015, US‑3)*
- **SC-004**: For each retained subject, the static connectivity‑strength metric is computed and saved; the difference (Exclusion – Inclusion) is correctly calculated and reported for the full cohort (≥ 10 subjects). *(See FR‑005, US‑2)*
- **SC-005**: ROI‑wise correlation‑matrix heatmaps for Inclusion and Exclusion conditions are generated, saved as PNG files, and include colorbars and axis labels. *(See FR‑017, US‑3)*
- **SC-006**: Dynamic connectivity‑strength series (sliding‑window) are produced for each condition, and summary statistics (mean and standard deviation across windows) are reported per subject. *(See FR‑018, US‑2)*

## Assumptions

- The OpenNeuro dataset `ds000030` (or an equivalent Cyberball task dataset) provides **preprocessed**, motion‑corrected fMRI data with clear “Inclusion” and “Exclusion” event markers within a single continuous run.  
- The Harvard‑Oxford atlas contains distinct, non‑overlapping masks for PCC, mPFC, and left/right angular gyrus that are already aligned to the preprocessed fMRI space.  
- The downloaded dataset contains at least **10** subjects after QC, satisfying the minimum sample size needed for a stable non‑parametric permutation test with 10 000 iterations.  
- All computations will run on a **CPU‑only** environment (e.g., GitHub Actions free‑tier runner) using standard scientific Python libraries (NumPy, SciPy, Nilearn, scikit‑learn). No GPU or CUDA dependencies are required.  
- Pearson correlation of raw BOLD time‑series is an appropriate metric for assessing task‑based functional connectivity within the DMN for the purposes of this hypothesis.  
- No synthetic or placeholder data will be generated; all metrics are derived exclusively from the real fMRI recordings and event timings.  
- The 0.2 mm motion threshold, 10‑subject minimum, and 10 000 permutation count are chosen to balance methodological rigor with the compute limits of the CI environment.  

--- 

**Paper‑stage handoff**: Upon successful completion of the research workflow, the generated tables, figures, and statistical summary will be packaged for downstream manuscript preparation. The paper pipeline will handle formatting, reference management, and submission; no additional engineering deliverables are required at this stage.