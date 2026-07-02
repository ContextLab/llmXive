# Feature Specification: Exploring the Relationship Between Brain Network Dynamics and Musical Creativity

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Exploring the Relationship Between Brain Network Dynamics and Musical Creativity"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully download resting-state fMRI data from specified OpenNeuro datasets (ds000224, ds000230), validate the presence of behavioral data and covariates, and preprocess it using standard neuroimaging tools (FSL/AFNI) to generate clean, normalized BOLD time series for graph analysis.

**Why this priority**: Without clean, preprocessed data and valid behavioral metadata, no subsequent graph metric calculation or correlation analysis is possible. This is the foundational data layer of the entire research pipeline.

**Independent Test**: Can be fully tested by executing the preprocessing script on a single subject's data and verifying the output files exist with expected dimensions and no motion-correction artifacts, without requiring behavioral data or graph analysis.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID and subject ID, **When** the preprocessing script is executed, **Then** the output directory contains motion-corrected, normalized, and bandpass-filtered (0.01-0.1 Hz) NIfTI files for that subject.
2. **Given** a subject with excessive head motion (>3mm translation), **When** the preprocessing script runs, **Then** the subject is flagged in a log file and excluded from the final analysis dataset.
3. **Given** the preprocessing pipeline completes, **When** the output is inspected, **Then** the time series length matches the original acquisition parameters minus the discarded initial volumes.
4. **Given** the dataset download, **When** the validation step runs, **Then** the system confirms the presence of at least one valid creativity proxy score and age/gender metadata, or halts with a clear error if missing.

---

### User Story 2 - Graph Metric Computation (Priority: P2)

The system must compute functional connectivity matrices and derive graph theoretical metrics (global efficiency, modularity, clustering coefficient) for each preprocessed subject using a standard brain atlas (e.g., Schaefer 200 ROI).

**Why this priority**: This step transforms raw time series into the specific predictor variables (integration/segregation metrics) required to answer the research question. It is independent of the behavioral correlation step.

**Independent Test**: Can be fully tested by running the metric computation on a pre-processed dataset and verifying that the output CSV contains the expected metric columns with valid numerical ranges (e.g., efficiency between 0 and 1), without needing behavioral scores.

**Acceptance Scenarios**:

1. **Given** a set of preprocessed BOLD time series and a defined ROI atlas, **When** the connectivity script runs, **Then** a symmetric correlation matrix is generated for each subject.
2. **Given** a correlation matrix, **When** the graph metric module executes, **Then** the output includes global efficiency, modularity (via Louvain algorithm), and clustering coefficient for each subject.
3. **Given** the graph metric computation completes, **When** the results are aggregated, **Then** the total number of subjects in the metric dataset matches the number of successfully preprocessed subjects.

---

### User Story 3 - Correlation Analysis and Reporting (Priority: P3)

The system must perform statistical correlation analysis between the computed graph metrics and creativity proxy scores (musical improvisation, TTCT, or AUT), applying appropriate multiple comparison corrections and generating visualization figures.

**Why this priority**: This is the final analytical step that directly addresses the research question. It depends on the successful completion of the previous two steps but delivers the primary scientific insight.

**Independent Test**: Can be fully tested by providing a synthetic dataset of graph metrics and behavioral scores to the analysis script and verifying that the output includes a correlation coefficient, p-value, effect size, and a scatter plot, even if the input data is dummy data.

**Acceptance Scenarios**:

1. **Given** a dataset containing graph metrics and corresponding creativity proxy scores, **When** the analysis script runs, **Then** Pearson or Spearman correlation coefficients are calculated for each metric-score pair.
2. **Given** multiple hypothesis tests are performed, **When** the correction step runs, **Then** p-values are adjusted using False Discovery Rate (FDR) correction and the adjusted values are reported.
3. **Given** the analysis completes, **When** the report is generated, **Then** it includes scatter plots with regression lines, 95% confidence intervals, and effect sizes (Cohen's d) for significant correlations.

---

### Edge Cases

- What happens when the OpenNeuro download fails due to network timeout? (System retries 3 times with exponential backoff, then logs a critical error and halts).
- How does the system handle subjects with missing behavioral scores? (Subjects are excluded from the correlation analysis but retained in the preprocessing and graph metric logs for auditability).
- What happens if the Louvain algorithm fails to converge on modularity for a sparse matrix? (The system falls back to a resolution parameter sweep across a range of candidate values and reports the resolution that maximizes modularity).
- What happens if age/gender metadata is missing for a subject? (The subject is excluded from the covariate-adjusted analysis but included in unadjusted analysis if specified).

## Requirements

### Functional Requirements

- **FR-001**: System MUST attempt to download resting-state fMRI data from OpenNeuro datasets ds000224 and ds000230. It MUST validate the presence of at least one valid creativity proxy score and age/gender metadata. If fewer than 50 subjects with valid data are found, the system MUST use all available subjects (N ≥ 1) for analysis. If NO subjects with valid data are found, the system MUST halt execution with a critical error stating 'No valid data found in specified datasets' (See US-1).
- **FR-002**: System MUST preprocess fMRI data using FSL/AFNI tools to perform motion correction, spatial normalization, and bandpass filtering (0.01-0.1 Hz) (See US-1).
- **FR-003**: System MUST compute functional connectivity matrices and graph metrics (global efficiency, modularity, clustering coefficient) using a 200-ROI atlas (See US-2).
- **FR-004**: System MUST perform Pearson/Spearman correlation analysis between graph metrics and creativity proxy scores using multiple linear regression to control for age and gender. If age/gender metadata is missing for a subject, that subject is excluded from the adjusted analysis. If no valid creativity proxy scores exist in the dataset, the system MUST halt with a critical error (See US-3).
- **FR-005**: System MUST apply False Discovery Rate (FDR) correction (Benjamini-Hochberg procedure) for multiple comparisons across all tested graph metrics and report effect sizes with 95% confidence intervals (See US-3).

### Key Entities

- **Subject**: Represents an individual participant, containing attributes for ID, age, gender, and file paths to preprocessed neuroimaging data.
- **GraphMetric**: Represents a computed network property (e.g., global efficiency) for a specific subject, containing the metric name, value, and associated confidence interval.
- **BehavioralScore**: Represents a creativity proxy assessment for a specific subject, containing the score_value, the source_type (e.g., 'musical_improvisation', 'TTCT', 'AUT'), and a list of sub_scale_names (e.g., 'fluency', 'originality') if available.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The preprocessing pipeline success rate is measured against the total number of downloaded subjects, targeting ≥ 90% completion (See US-1).
- **SC-002**: The correlation analysis process is measured against the requirement that the script completes successfully and reports correlation coefficients, p-values, and effect sizes for all tested metric-score pairs (See US-3).
- **SC-003**: The effect size calculation is measured against the requirement that Cohen's d (or equivalent) is correctly calculated and reported for all significant correlations (See US-3).
- **SC-004**: The multiple comparison correction is measured against the requirement that all reported p-values are adjusted using FDR (Benjamini-Hochberg) to control the false discovery rate (See US-3).
- **SC-005**: The computational resource usage is measured against the constraint of ≤ 7 GB RAM and ≤ 6 hours total runtime on a GitHub Actions 2-core runner (See US-2, US-3).

## Assumptions

- The OpenNeuro datasets (ds000224, ds000230) contain resting-state fMRI data.
- The system MUST validate the presence of behavioral data (musical improvisation, TTCT, or AUT) and age/gender metadata within these specific datasets. If these datasets lack a direct musical improvisation task or standard proxies (TTCT/AUT), the system MUST halt execution with a critical error stating 'No valid creativity proxy found in specified datasets' rather than inferring a measure or assuming external benchmarks exist within the dataset.
- The 200-ROI Schaefer atlas is appropriate for the resolution of the downloaded fMRI data and provides sufficient granularity for graph metric computation.
- The available CPU-only GitHub Actions runner environment (multiple cores, sufficient RAM) is sufficient to run FSL/AFNI preprocessing and NetworkX graph analysis on the sampled dataset within the 6-hour limit.
- The False Discovery Rate (FDR) correction method is appropriate for the number of graph metrics tested, accounting for potential multicollinearity between metrics.
- If specific sub-scales (e.g., 'originality') are unavailable in the behavioral data, the system uses the aggregate score and reports this limitation in the analysis output.