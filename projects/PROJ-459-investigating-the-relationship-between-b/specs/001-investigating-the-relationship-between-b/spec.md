# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

**Feature Branch**: `001-brain-music-preference`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference"

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Validation, and Preprocessing (Priority: P1)

The system MUST successfully download resting-state fMRI data and associated behavioral metadata from OpenNeuro, validate the presence of specific behavioral variables, preprocess the fMRI data using fMRIPrep, and extract regional time courses using the Schaefer-400 atlas.

**Why this priority**: Without valid, preprocessed neural and behavioral data, no analysis can occur. This is the foundational data pipeline required for all downstream metrics.

**Independent Test**: The pipeline can be tested by verifying the existence of preprocessed BOLD time series files and a merged CSV containing subject IDs, network metrics (placeholder), and genre preference scores for a subset of subjects (e.g., 10 subjects), AND verifying that the system correctly flags or falls back when the primary behavioral variable is missing.

**Acceptance Scenarios**:
1. **Given** a valid OpenNeuro dataset ID (e.g., ds000030), **When** the ingestion script runs, **Then** fMRIPrep outputs (preprocessed BOLD, confounds) exist for all available subjects, and behavioral metadata is successfully merged with subject IDs.
2. **Given** preprocessed BOLD files, **When** the Schaefer-400 atlas extraction runs, **Then** a matrix of regional time courses (subjects × 400 ROIs × timepoints) is generated without errors.
3. **Given** the merged dataset, **When** the system checks for missing values, **Then** subjects with >10% missing behavioral data or >10% corrupted fMRI volumes are flagged and excluded from the final analysis list.
4. **Given** a dataset where the primary 'musical genre preference' variable is missing, **When** the system validates the schema, **Then** it MUST automatically switch to the 'STOMP-R' proxy variable if available, or halt execution with a clear error code `ERR_DATA_MISSING` and log the specific missing field name.

---

### User Story 2 - Static and Dynamic Network Metric Computation with Sensitivity Analysis (Priority: P2)

The system MUST compute static functional connectivity matrices and derived network metrics (global efficiency, modularity, within-module degree) as well as dynamic reconfiguration metrics using sliding-window analysis for each valid subject. The system MUST also perform a sensitivity analysis on the sliding-window parameters.

**Why this priority**: This transforms raw time series into the specific predictor variables (neural architecture) required to test the research hypothesis. Sensitivity analysis ensures the dynamic metrics are robust to parameter choice.

**Independent Test**: The computation can be tested by running the metric calculation on a small synthetic time-series dataset and verifying that the output CSV contains the expected columns (e.g., `global_efficiency`, `modularity_Q`, `dynamic_reconfiguration_rate`) with numeric values within plausible ranges. The sensitivity analysis is tested by verifying that the system runs the pipeline with window sizes of 20, 30, and 40 TRs and reports the correlation stability of the resulting metrics.

**Acceptance Scenarios**:
1. **Given** regional time courses for a subject, **When** static connectivity is calculated, **Then** a symmetric 400x400 correlation matrix is generated, and network metrics are derived using standard graph-theory formulas.
2. **Given** regional time courses, **When** sliding-window analysis runs (window=30 TRs, step=5 TRs), **Then** a dynamic connectivity time-series is generated, and the mean reconfiguration rate is calculated.
3. **Given** the computed metrics, **When** the system aggregates results, **Then** a single row per subject is created in the analysis dataset containing all static and dynamic metrics alongside their behavioral scores.
4. **Given** the analysis pipeline, **When** the sensitivity analysis runs, **Then** the system executes the dynamic metric calculation with window sizes of 20, 30, and 40 TRs, and outputs a stability report showing the intraclass correlation coefficient (ICC) of the dynamic metrics across these window sizes.

---

### User Story 3 - Statistical Correlation, Power Analysis, and Visualization (Priority: P3)

The system MUST perform Spearman correlations between each network metric and each genre preference score, apply Benjamini-Hochberg correction, conduct a power analysis, and generate visualization figures (heatmaps, network diagrams) and statistical summary tables.

**Why this priority**: This delivers the final scientific output: the evidence linking neural architecture to musical taste, satisfying the research question. Power analysis ensures the study can distinguish between 'no relationship' and 'insufficient data'.

**Independent Test**: The analysis can be tested by running the correlation module on a mock dataset with known correlations and verifying that the output table correctly identifies significant correlations (p<0.05) and that the Benjamini-Hochberg adjusted p-values are calculated correctly. Power analysis is tested by verifying the system reports the achieved power (≥0.8) for the sample size and effect size observed.

**Acceptance Scenarios**:
1. **Given** the analysis dataset, **When** the correlation module runs, **Then** a matrix of Spearman correlation coefficients and raw p-values is generated for all metric-genre pairs.
2. **Given** the raw p-values, **When** the Benjamini-Hochberg correction is applied, **Then** adjusted p-values are calculated, and significant pairs are flagged (adjusted p < 0.05).
3. **Given** the significant results, **When** the visualization module runs, **Then** a correlation heatmap and at least one network diagram highlighting significant connections are generated as PNG/PDF files.
4. **Given** the sample size and observed effect size, **When** the power analysis runs, **Then** the system calculates the achieved power and reports whether it meets the ≥0.8 threshold. If power < 0.8, the system flags the result as 'Underpowered' in the final report.

### Edge Cases

- What happens when the OpenNeuro dataset lacks the specific behavioral questionnaire required for genre preference? (System MUST log the specific missing field, attempt fallback to STOMP-R, and if that fails, halt with `ERR_DATA_MISSING`).
- How does the system handle subjects with excessive head motion (>0.5mm FD) which invalidates resting-state connectivity? (System MUST exclude these subjects and report the exclusion count).
- What happens if the Benjamini-Hochberg correction results in zero significant findings? (System MUST still generate the full results table and visualization, explicitly stating "No significant correlations found after correction", and report the achieved power).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data and behavioral metadata from OpenNeuro for specified datasets (e.g., ds000030, ds000208) and merge them by subject ID. (See US-1)
- **FR-001b**: System MUST validate the presence of the 'musical genre preference' variable; if missing, it MUST automatically switch to the 'STOMP-R' proxy variable if available, or halt with error `ERR_DATA_MISSING`. (See US-1)
- **FR-002**: System MUST preprocess fMRI data using fMRIPrep (Docker) to generate standardized BOLD time series and confound regressors. (See US-1)
- **FR-003**: System MUST extract regional time courses using the Schaefer-400 atlas to create a 400-ROI parcellation for each subject. (See US-1)
- **FR-004**: System MUST calculate static functional connectivity metrics (global efficiency, modularity, within-module degree) for DMN, auditory, and salience networks. These networks MUST be identified by mapping the Schaefer-400 ROIs to the Yeo 7-network parcellation (DMN=7, Auditory=4, Salience=2) using the official Schaefer lookup table. (See US-2)
- **FR-005**: System MUST compute dynamic functional connectivity using a sliding-window approach (window=30 TRs, step=5 TRs) to derive reconfiguration metrics. (See US-2)
- **FR-006**: System MUST perform Spearman rank correlations between every network metric and every musical genre preference score. (See US-3)
- **FR-007**: System MUST apply Benjamini-Hochberg correction to all correlation p-values to control the false discovery rate across the family of tests. (See US-3)
- **FR-008**: System MUST generate a correlation heatmap and network diagrams highlighting statistically significant findings (adjusted p < 0.05). (See US-3)
- **FR-009**: System MUST perform a post-hoc power analysis for the primary correlation tests to determine if the sample size (N) is sufficient to detect an effect size of |r| ≥ 0.3 with power ≥ 0.8. (See US-3)
- **FR-010**: System MUST validate the metric calculation pipeline against a null distribution by running the correlation on a dataset with randomized behavioral labels (100 permutations) and verifying the observed false positive rate is ≤ 0.05. (See US-3)
- **FR-011**: System MUST perform a sensitivity analysis on the sliding-window parameters by re-running the dynamic metric calculation with window sizes of 20, 30, and 40 TRs, and reporting the stability (ICC ≥ 0.7) of the dynamic metrics across these parameters. (See US-2)

### Key Entities

- **Subject**: Represents an individual participant, containing unique ID, demographic data, and genre preference scores.
- **TimeSeries**: Represents the BOLD signal for a specific ROI, containing timepoint values and metadata.
- **NetworkMetric**: Represents a derived graph theory measure (e.g., global efficiency) for a specific subject and network. The network is defined by the mapping of Schaefer-400 ROIs to the Yeo 7-network parcellation (DMN=7, Auditory=4, Salience=2).
- **CorrelationResult**: Represents the statistical relationship between a specific metric and a specific genre, containing coefficient, raw p-value, and adjusted p-value.
- **SensitivityReport**: Represents the stability analysis of dynamic metrics across different sliding-window parameters.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of subjects successfully preprocessed and included in the final analysis is measured against the total number of subjects available in the OpenNeuro dataset. The system MUST achieve ≥80% successful preprocessing rate. (See US-1)
- **SC-002**: The computational runtime of the full pipeline (preprocessing + metrics + correlation) is measured against the 6-hour limit of the free-tier GitHub Actions runner for a load profile of N=50 subjects. (See US-2, US-3)
- **SC-003**: The validity of the Benjamini-Hochberg correction is measured by verifying that the proportion of false positives in a null-simulation dataset (randomized labels) is ≤ 0.05. (See US-3)
- **SC-004**: The reproducibility of the correlation results is measured by re-running the analysis on a held-out subset of data (if sample size permits) or by verifying the stability of coefficients across bootstrap resamples (a sufficient number of iterations). (See US-3)
- **SC-005**: The accuracy of the network metric calculation is measured against internal consistency (test-retest reliability) on a subset of subjects with repeated scans, requiring an Intraclass Correlation Coefficient (ICC) ≥ 0.7. (See US-2)
- **SC-006**: The achieved statistical power for the primary correlation tests is measured against the target threshold of ≥0.8 for an effect size of |r| ≥ 0.3. (See US-3)

## Assumptions

- The OpenNeuro datasets (ds000030, ds000208) contain either the specific behavioral questionnaire measuring musical genre preference or the STOMP-R proxy. If neither is present, the system halts with `ERR_DATA_MISSING` and the research question is deemed untestable with the current data source.
- The fMRIPrep Docker container can be successfully pulled and executed on a CPU-only GitHub Actions runner with sufficient RAM without exceeding memory limits.; if memory errors occur, the pipeline will automatically downsample the fMRI resolution or use a subset of ROIs.
- The sliding-window analysis (window=30 TRs, step=5 TRs) is computationally feasible within the 6-hour runtime limit for the full dataset; if the dataset size exceeds this, the analysis will be restricted to a random sample of 50 subjects.
- The Schaefer-400 atlas is appropriate for the resolution of the downloaded fMRI data; if the data resolution is significantly lower, the analysis will default to a coarser atlas (e.g., Schaefer-200) to maintain signal quality.
- The Benjamini-Hochberg correction is sufficient for the family-wise error rate control required; if the number of tests is extremely large (e.g., >10,000), a more conservative Bonferroni correction may be considered as a sensitivity analysis.
- No GPU acceleration is available or required; all fMRI preprocessing and network metric calculations are performed using CPU-optimized libraries (e.g., Nilearn, NetworkX, Scikit-learn) in default precision.
- The Yeo 7-network parcellation mapping for the Schaefer-400 atlas is the standard definition for DMN, Auditory, and Salience networks in this context.
