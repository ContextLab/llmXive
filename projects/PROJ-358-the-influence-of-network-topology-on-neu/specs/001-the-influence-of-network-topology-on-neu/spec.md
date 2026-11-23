# Feature Specification: The Influence of Network Topology on Neural Synchrony During Cognitive Tasks

**Feature Branch**: `001-the-influence-of-network-topology-on-neu`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does the baseline topological organization of resting-state brain networks relate to the degree of neural synchrony exhibited during working memory task performance?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher needs to automatically download, preprocess, and parcellate resting-state and task-based fMRI data for a specific subset of subjects from the Human Connectome Project (HCP) to ensure the analysis is reproducible and fits within the 6-hour compute window.

**Why this priority**: Without clean, preprocessed data, no analysis can occur. This is the foundational step. The constraint of running on free-tier CPU (a limited number of cores, ~7GB RAM) dictates that the preprocessing must be efficient and the dataset size strictly limited to avoid out-of-memory errors.

**Independent Test**: Can be fully tested by running the data pipeline script on a single subject and verifying that the output consists of a cleaned 4D NIfTI file and a corresponding 200-region time-series CSV, with motion parameters within acceptable bounds (frame displacement < 0.5mm). The pipeline must also verify that the total download size for a representative cohort of subjects does not exceed a predefined storage threshold.

**Acceptance Scenarios**:

1. **Given** a valid HCP subject ID, **When** the pipeline executes the download and preprocessing steps, **Then** the system outputs a parcellated time-series matrix (200 regions x timepoints) and a motion parameter file for both resting-state and working-memory task scans.
2. **Given** a subject with excessive motion (frame displacement > 0.5mm), **When** the pipeline processes the data, **Then** the system flags the subject for exclusion and logs the exclusion reason without crashing the batch job.
3. **Given** the full dataset size, **When** the pipeline runs on a CPU-only runner with 7GB RAM, **Then** the memory usage never exceeds 6.5 GB, the total processing time for 100 subjects remains ≤ 3.5 hours, and the total downloaded data size does not exceed a manageable threshold..

---

### User Story 2 - Graph Metric and Synchrony Calculation (Priority: P2)

The researcher needs to compute resting-state graph-theoretical metrics (clustering coefficient, characteristic path length, global efficiency, modularity) and task-based neural synchrony (Mean Functional Connectivity) for the parcellated data to generate the predictor and outcome variables for the correlation analysis.

**Why this priority**: This step transforms raw time-series into the specific variables required by the research question. It must be robust to the specific definitions of the metrics (e.g., thresholding methods) and must run entirely on CPU without GPU acceleration.

**Independent Test**: Can be fully tested by running the calculation module on the preprocessed time-series of 5 subjects and verifying that the output CSV contains the specific graph metrics and connectivity values with no NaN entries and values within theoretical bounds (e.g., efficiency ∈ [0, 1]). The calculation must complete within a reasonable time budget.

**Acceptance Scenarios**:

1. **Given** a resting-state time-series matrix, **When** the graph analysis module runs with the default 20% proportional threshold, **Then** it outputs a row of data containing the global clustering coefficient, characteristic path length, global efficiency, and modularity.
2. **Given** task-based fMRI time-series during working memory epochs, **When** the synchrony module runs, **Then** it calculates the mean Functional Connectivity (Pearson correlation) across all region pairs for the frontoparietal and default mode networks.
3. **Given** the computational constraints (no GPU), **When** the calculation runs, **Then** it utilizes vectorized CPU operations (e.g., via NumPy/SciPy) and completes the calculation for 100 subjects in ≤ 2 hours.

---

### User Story 3 - Statistical Association and Sensitivity Analysis (Priority: P3)

The researcher needs to perform Pearson correlation analyses between resting-state topology and task-based synchrony, apply multiple-comparison corrections, and conduct a sensitivity analysis on any introduced thresholds to validate the robustness of the findings.

**Why this priority**: This is the core scientific inquiry. It must adhere to methodological soundness (associational framing, multiplicity correction) and include sensitivity checks for any arbitrary thresholds to satisfy the methodology panel.

**Independent Test**: Can be fully tested by running the statistical module on the generated metrics and verifying that the output includes correlation coefficients, p-values, FDR-corrected q-values, and a sensitivity report showing how results vary across a swept threshold range.

**Acceptance Scenarios**:

1. **Given** the dataset of graph metrics and synchrony values, **When** the statistical module runs, **Then** it outputs Pearson correlation coefficients and p-values for each metric pair, explicitly labeled as "associational" rather than causal.
2. **Given** multiple hypothesis tests (e.g., 4 metrics × 2 networks), **When** the correction step runs, **Then** it applies False Discovery Rate (FDR) correction and reports the adjusted q-values for each test.
3. **Given** a specific decision cutoff (e.g., a proportional threshold for network construction), **When** the sensitivity analysis runs, **Then** it sweeps the cutoff over {0.10, 0.20, 0.30} and reports the variation in the correlation coefficient and significance status for each sweep point.

---

### Edge Cases

- **What happens when** the HCP API returns a 429 (Too Many Requests) error during the batch download?
  - *System handles*: The pipeline implements an exponential backoff retry strategy with a limited number of attempts and increasing delays before failing the specific subject and continuing with the next.
- **How does system handle** a subject where the task-based fMRI scan is missing or corrupted?
  - *System handles*: The pipeline detects the missing file, logs the error, excludes the subject from the final correlation analysis, and generates a report of excluded subjects.
- **What happens when** the calculated graph metrics result in a singular matrix or undefined values (e.g., infinite path length in a disconnected graph)?
 - *System handles*: The calculation module validates that the proportional thresholding step (FR-003a) has produced a connected graph; if the graph is disconnected at the default threshold (20%), it logs a warning and attempts the next higher threshold in the sensitivity range ([deferred]) for that specific subject, flagging the subject in the log if no connected graph is found.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download resting-state and task-based fMRI data for exactly N=100 subjects from the HCP dataset via API, ensuring total data size fits within 14 GB disk space. (See US-1)
- **FR-002**: System MUST preprocess fMRI data including motion correction, spatial normalization to MNI space, temporal filtering within a low-frequency band, and nuisance regression, outputting a 200-region parcellated time-series. (See US-1)
- **FR-003a**: System MUST construct the adjacency matrix by applying a proportional threshold to the Pearson correlation matrix, retaining a substantial subset of the strongest edges, with a default threshold for primary calculations. (See US-2)
- **FR-003b**: System MUST calculate resting-state graph-theoretical metrics (clustering coefficient, characteristic path length, global efficiency, modularity) using the thresholded adjacency matrix from FR-003a. (See US-2)
- **FR-004**: System MUST compute task-based neural synchrony using Mean Functional Connectivity (Pearson correlation) between region pairs specifically during working memory task epochs, aggregated by network (frontoparietal, default mode). (See US-2)
- **FR-005**: System MUST perform Pearson correlation analysis between resting-state topology metrics and task-based synchrony metrics, framing results as associational relationships only. (See US-3)
- **FR-006**: System MUST apply False Discovery Rate (FDR) correction for the family of hypothesis tests performed (≥4 metrics × 2 networks) to control family-wise error. (See US-3)
- **FR-007**: System MUST execute a sensitivity analysis sweeping the network construction proportional threshold over the set {0.10, 0.20, 0.30} and report the resulting variation in correlation coefficients. (See US-3)

### Key Entities

- **Subject**: Represents a single individual in the HCP dataset, identified by a unique ID, containing associated resting-state and task-based fMRI files.
- **TimeSeries**: A 2D matrix (Regions x Timepoints) representing the BOLD signal intensity for 200 brain regions after preprocessing and parcellation.
- **GraphMetric**: A structured record containing the calculated values for clustering coefficient, characteristic path length, global efficiency, and modularity for a specific subject.
- **SynchronyMetric**: A structured record containing the mean Functional Connectivity (Pearson correlation) for specific network pairs (e.g., Frontoparietal-DefaultMode) during task epochs.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation analysis output must contain a valid Pearson correlation coefficient (r) and p-value for the relationship between global efficiency and frontoparietal connectivity, measured against the computed dataset. (See FR-005, US-3)
- **SC-002**: The final results table must include FDR-corrected q-values for all tested metric pairs, measured against the uncorrected p-values to demonstrate multiplicity control. (See FR-006, US-3)
- **SC-003**: The sensitivity analysis report must show the correlation coefficient (r) and significance status (p < 0.05) for each of the three threshold values {0.10, 0.20, 0.30}, measured against the stability of the headline finding. (See FR-007, US-3)
- **SC-004**: The total runtime of the analysis pipeline (download to final plot) must be ≤ 6 hours, measured against a fixed internal budget of 6 hours. (See FR-001, US-1)
- **SC-005**: The memory usage of the preprocessing and calculation steps must not exceed the allocated system capacity at any point., measured as peak Resident Set Size (RSS) via /proc/self/status against the 7 GB RAM constraint of the free-tier runner. (See FR-002, US-1)

## Assumptions

- The Human Connectome Project (HCP) API provides programmatic access to the required resting-state and working-memory task fMRI data for N≈100 subjects without requiring complex authentication beyond standard API keys.
- The "200-region Schaefer atlas" is available as a standard parcellation file compatible with the HCP data resolution (MNI space).
- The Mean Functional Connectivity calculation can be performed efficiently on CPU using vectorized operations (e.g., NumPy) without requiring the FFT-based optimizations that typically demand GPU acceleration for large datasets.
- The relationship between resting-state topology and task-based synchrony is strictly associational; no causal inference (e.g., mediation analysis with instrumental variables) is attempted in this initial pass.
- The dataset provided by HCP contains all necessary variables (BOLD time-series for both states) and does not require imputation for missing regions or timepoints.
- The "working memory task epochs" can be reliably isolated from the task-based fMRI data using the provided event timing files in the HCP metadata.
- The FDR correction method (Benjamini-Hochberg) is sufficient for the number of tests performed (≤ 10) and does not require more conservative methods like Bonferroni which might obscure true effects.
- The sensitivity analysis threshold sweep {0.10, 0.20, 0.30} is sufficient to demonstrate the robustness of the findings without requiring an exhaustive grid search.
- Proportional thresholding (retaining the top 10-30% of edges) is the standard method for constructing sparse, connected graphs from fMRI correlation matrices, ensuring valid calculation of path length and other global metrics.