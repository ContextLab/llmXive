# Feature Specification: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

**Feature Branch**: `001-investigating-relationship-between-brain-network`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system must successfully download resting-state fMRI data for at least 50 subjects from a cohort recruited for this study (using HCP acquisition protocols), preprocess it using fMRIPrep to correct for motion and nuisance signals, and extract BOLD time series from Schaefer ROIs.

**Why this priority**: This is the foundational data layer. Without clean, standardized neural data, no topology metrics can be computed, and no correlation with behavioral data is possible. This is the prerequisite for all subsequent analysis.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a subset of 5 subjects and verifying that the output contains valid time-series matrices for 200 ROIs with no NaN values and motion parameters below the exclusion threshold (FD < 0.5mm).

**Acceptance Scenarios**:

1. **Given** the study recruitment credentials are valid and the network is connected, **When** the download script executes, **Then** the system retrieves at least 50 subject folders containing resting-state fMRI NIfTI files.
2. **Given** raw fMRI data exists for a subject, **When** fMRIPrep is executed with the standard HCP configuration, **Then** the output includes a preprocessed NIfTI file, a confound regressors TSV file, and a successful completion log without errors.
3. **Given** a preprocessed fMRI file and the Schaefer 200 parcellation map, **When** the time-series extraction script runs, **Then** a 200xT matrix is generated where T is the number of timepoints, and the mean framewise displacement is recorded.

---

### User Story 2 - Network Topology Metric Computation (Priority: P2)

The system must compute functional connectivity matrices (Pearson correlation) for each subject and derive five specific graph theory metrics: modularity (via Louvain with fixed seed), characteristic path length, clustering coefficient, global efficiency, and small-worldness.

**Why this priority**: This transforms raw time-series data into the specific "predictor" variables required to test the hypothesis. It bridges the gap between raw neuroimaging and the abstract concept of "topology."

**Independent Test**: The metric computation can be tested on a single subject's connectivity matrix to verify that the output values fall within the theoretical bounds for each metric (e.g., path length > 0, modularity between 0 and 1) and that the Louvain algorithm converges within 100 iterations.

**Acceptance Scenarios**:

1. **Given** a valid 200x200 functional connectivity matrix, **When** the graph metric calculator runs, **Then** it outputs a JSON object containing `modularity`, `path_length`, `clustering_coefficient`, `global_efficiency`, and `small_worldness`.
2. **Given** a connectivity matrix, **When** the Louvain algorithm is invoked with a fixed random seed to ensure reproducibility., **Then** the community detection completes within 30 minutes on a standard CPU and returns a partition (which may be a single module if optimal).
3. **Given** a set of computed metrics, **When** the system validates the output, **Then** it flags any subject where `global_efficiency` exceeds 1.0 or `path_length` is non-positive as an outlier for manual review.

---

### User Story 3 - Correlation Analysis and Statistical Reporting (Priority: P3)

The system must correlate the computed topology metrics with visual illusion susceptibility scores (Müller-Lyer and Ponzo), apply Benjamini-Hochberg FDR correction for multiple comparisons, and generate scatter plots with regression lines for significant findings.

**Why this priority**: This addresses the core research question. It synthesizes the neural data and the behavioral data to produce the final scientific result. It is the "value delivery" of the research.

**Independent Test**: The analysis can be tested by injecting a synthetic dataset where a known correlation exists between a metric and the illusion score, verifying that the script correctly identifies the p-value < 0.05 and flags it as significant after FDR correction.

**Acceptance Scenarios**:

1. **Given** a CSV containing subject IDs, topology metrics, and illusion scores, **When** the correlation analysis runs, **Then** it outputs a table of Pearson/Spearman correlation coefficients, p-values, and FDR-adjusted p-values for all 10 metric-illusion pairs (5 metrics x 2 illusions).
2. **Given** a pair of variables with an FDR-adjusted p-value < 0.05, **When** the visualization script runs, **Then** it generates a scatter plot with a regression line, % confidence interval shading, and the correlation coefficient annotated.
3. **Given** the full set of results, **When** the report is generated, **Then** it explicitly states whether any hypothesis was rejected or if the result is null, including effect sizes (Cohen's d or r) for all tested pairs regardless of significance.

---

### User Story 4 - Behavioral Data Collection (Priority: P1)

The system must provide a custom online psychophysical task to collect visual illusion susceptibility scores (Müller-Lyer and Ponzo) from study participants, linking these scores to their unique Study ID.

**Why this priority**: The behavioral data (Y variable) is not available in existing public datasets like HCP. This user story ensures the mechanism exists to acquire the necessary outcome data to pair with the neural data, closing the data independence gap.

**Independent Test**: The task can be tested by running a simulation where a known "subject" completes the illusion tasks, verifying that the system correctly records the scores and associates them with the provided Study ID.

**Acceptance Scenarios**:

1. **Given** a valid Study ID is provided, **When** a participant completes the Müller-Lyer task, **Then** the system records the susceptibility score and links it to the Study ID in the database.
2. **Given** a valid Study ID is provided, **When** a participant completes the Ponzo task, **Then** the system records the susceptibility score and links it to the Study ID in the database.
3. **Given** a participant has completed both tasks, **When** the data export script runs, **Then** it generates a CSV containing the Study ID, Müller-Lyer score, and Ponzo score for all completed sessions.

---

### Edge Cases

- **Missing Behavioral Data**: What happens if a subject has valid fMRI data but missing or incomplete illusion scores? The system must exclude the subject from the correlation analysis but retain them in the preprocessing log for transparency.
- **Network Disconnectedness**: How does the system handle a functional connectivity matrix that results in a disconnected graph (infinite path length)? The system must replace infinite path lengths with a sentinel value (e.g., `NaN`) and exclude that specific metric for that subject from the correlation, logging the event.
- **FDR Correction Failure**: What if the number of significant uncorrected tests is zero? The system must still generate the full results table and explicitly state "No significant correlations found after FDR correction" rather than failing or returning an empty report.
- **Single Module Partition**: What if the Louvain algorithm determines that the optimal community structure for a subject is a single module (modularity = 0)? The system must record the calculated modularity value (which may be 0) without forcing an artificial partition, and include this value in the analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data for a minimum of 50 subjects from a study cohort (using HCP protocols) and store them in a local directory structure organized by subject ID (See US-1).
- **FR-002**: System MUST execute fMRIPrep with motion correction, normalization to MNI space, and nuisance regression (including white matter, CSF, and global signal) to produce preprocessed BOLD time series (See US-1).
- **FR-003**: System MUST extract BOLD time series from Schaefer ROIs (See US-1) and compute a 200x200 Pearson correlation matrix for each subject (See US-2).
- **FR-004**: System MUST calculate five graph theory metrics per subject: modularity (Louvain algorithm, fixed seed), characteristic path length, clustering coefficient, global efficiency, and small-worldness (See US-2).
- **FR-005**: System MUST perform Pearson or Spearman correlation between each of the 5 topology metrics and 2 illusion susceptibility scores (Müller-Lyer, Ponzo) resulting in a set of total tests, and apply Benjamini-Hochberg FDR correction (See US-3).
- **FR-006**: System MUST generate scatter plots with regression lines and confidence intervals for any metric-illusion pair where the FDR-adjusted p-value is < 0.05 (See US-3).
- **FR-007**: System MUST explicitly frame all reported findings as "associational" and avoid causal language in the final output text unless randomization is explicitly documented (See US-3).
- **FR-008**: System MUST implement a custom online psychophysical task to collect Müller-Lyer and Ponzo illusion scores, accepting a unique Study ID to link behavioral data to the corresponding subject (See US-4).

### Key Entities

- **Subject**: Represents an individual participant in the study, containing unique ID, Study ID, raw fMRI file paths, preprocessed time-series data, and behavioral scores.
- **ConnectivityMatrix**: A 200x200 symmetric matrix representing functional connectivity strength between all pairs of Schaefer ROIs for a single subject.
- **TopologyMetrics**: A record containing the five computed graph metrics (modularity, path length, clustering coefficient, global efficiency, small-worldness) for a single subject.
- **IllusionScore**: A record containing the susceptibility scores for the Müller-Lyer and Ponzo illusions for a single subject.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of subjects with valid preprocessed data (motion < 0.5mm FD) is measured against the total number of downloaded subjects to ensure data quality (See US-1).
- **SC-002**: The computational runtime for graph metric extraction per subject is measured against the CI job time limit to ensure feasibility on CPU-only hardware (See US-2).
- **SC-003**: The number of significant correlations (FDR-adjusted p < 0.05) is measured against the null hypothesis of no relationship to determine if the study yields a positive result (See US-3).
- **SC-004**: The effect size (r or Cohen's d) for the strongest correlation is measured against the confidence interval to assess the magnitude of the association (See US-3).
- **SC-005**: The reproducibility of the pipeline is measured by re-running the analysis on a subset of subjects (by ID) of the dataset and verifying that the correlation coefficients match within a tolerance of [deferred] (See US-3).

## Assumptions

- **Dataset Variable Fit**: The study will recruit a new cohort of n≥50 subjects. For these subjects, both resting-state fMRI (using HCP protocols) and visual illusion scores (via the custom task) will be collected, ensuring a valid population where both variables are measured. The HCP release data is used as a protocol template, not the direct data source for this specific correlational study.
- **Inference Framing**: The study design is observational (correlational) using existing or newly collected data; therefore, all conclusions must be framed as associational relationships between network topology and perceptual bias, not causal mechanisms.
- **Compute Feasibility**: The analysis of a cohort of subjects with a representative set of ROIs using fMRIPrep and Brain Connectivity Toolbox will fit within the available RAM and time limit of a standard GitHub Actions free-tier runner without requiring GPU acceleration.
- **Threshold Justification**: The significance threshold for FDR correction is fixed at q < 0.05 based on standard neuroimaging conventions; a sensitivity analysis will sweep the threshold across a range of representative values to ensure robustness of the headline findings.
- **Measurement Validity**: The Schaefer parcellation is assumed to provide a valid and citable definition of cortical nodes for the functional network construction, consistent with the literature on ROI definition methodology.
- **Predictor Collinearity**: The five graph metrics (modularity, path length, clustering, efficiency, small-worldness) are assumed to capture distinct topological features; however, a collinearity diagnostic (VIF < 5) will be performed to ensure they are not definitionally redundant before inclusion in the correlation analysis.