# Feature Specification: The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

**Feature Branch**: `001-impact-of-network-centrality-on-neural-synchrony`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Do structural-connectivity-derived centrality metrics (from diffusion MRI) predict the magnitude of functional synchrony measured from resting-state fMRI?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

**Description**: The researcher MUST be able to download a subset of **OpenNeuro ds000224** (HCP Young Adult subset, max 10 subjects), preprocess fMRI BOLD time series and diffusion MRI tractography, and generate a parcellated structural and functional connectivity matrix for each subject using the Schaefer atlas.

**Why this priority**: Without clean, matched structural and functional data matrices, no analysis can occur. This is the foundational data preparation step required for all subsequent statistical testing.

**Independent Test**: The pipeline can be fully tested by verifying that for a **single subject from OpenNeuro ds000224**, the script outputs a valid structural adjacency matrix (400x400) and a functional correlation matrix of the same dimensions, with no missing values due to preprocessing failures.

**Acceptance Scenarios**:
1. **Given** raw data from OpenNeuro ds000224 for a subject, **When** the preprocessing script runs, **Then** it outputs a clean structural connectivity matrix and a functional connectivity matrix in the project's `data/processed` directory.
2. **Given** a subject with motion artifacts exceeding 0.5mm, **When** the script applies motion correction and nuisance regression, **Then** the resulting time series have a framewise displacement below the 0.5mm threshold or the subject is flagged for exclusion in the log.

---

### User Story 2 - Centrality and Synchrony Metric Computation (Priority: P2)

**Description**: The researcher MUST be able to compute node-level centrality metrics (degree, betweenness, eigenvector) from the structural matrices and mean functional synchrony (average absolute correlation) from the functional matrices for every brain region (ROI) in the atlas.

**Why this priority**: This transforms raw connectivity matrices into the specific predictor (centrality) and outcome (synchrony) variables required for the regression analysis.

**Independent Test**: The computation can be fully tested by running the metric calculator on a small synthetic graph and verifying that the output matches known mathematical properties (e.g., a node with no edges has degree centrality of 0).

**Acceptance Scenarios**:
1. **Given** a thresholded structural connectivity matrix, **When** the centrality calculator runs, **Then** it outputs a CSV file containing degree, betweenness, and eigenvector centrality for all ROIs.
2. **Given** a functional correlation matrix, **When** the synchrony calculator runs, **Then** it outputs a CSV file containing the mean absolute correlation (synchrony strength) for all ROIs.

---

### User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Description**: The researcher MUST be able to perform a Spearman correlation between structural centrality and functional synchrony, apply permutation testing (n=1000) to correct for multiple comparisons, and generate a scatter plot with regression lines and confidence intervals.

**Why this priority**: This delivers the final research answer (the correlation coefficient and p-value) and the visual evidence required to validate the hypothesis.

**Independent Test**: The analysis can be fully tested by running the script on a shuffled dataset (where the relationship is known to be null) and verifying that the p-value > 0.05 and the plot shows no significant trend.

**Acceptance Scenarios**:
1. **Given** the computed centrality and synchrony vectors, **When** the analysis script runs, **Then** it outputs a JSON report containing the Spearman rho, p-value (uncorrected and permutation-corrected), and effect size (Spearman's rho and Fisher's z-transformed 95% CI).
2. **Given** the statistical results, **When** the visualization module runs, **Then** it generates a high-resolution PNG scatter plot with the regression line, 95% confidence interval, and a text annotation of the p-value.

---

### Edge Cases

- **What happens when** the OpenNeuro ds000224 download fails or a subject file is corrupted? The pipeline MUST skip the corrupted subject, log a warning, and proceed with the remaining valid subjects (minimum n=10 required to proceed). If fewer than 10 valid subjects are available, the pipeline MUST halt with a fatal error.
- **What happens when** the runner storage fills up during the extraction of raw NIfTI files? The pipeline MUST detect disk usage approaching a high threshold (leaving a buffer)., stop downloading new subjects, process the currently downloaded subjects, and if the total valid count is < 10, halt with a "Storage Limit Exceeded" error.
- **How does the system handle** a structural matrix where the number of nodes does not match the functional matrix (e.g., due to atlas mismatch)? The system MUST halt execution with a clear error message identifying the dimension mismatch before attempting any correlation.
- **What happens when** the permutation test p-value is exactly 0 (all permutations yield a lower correlation)? The system MUST report p < 1/1000 (0.001) rather than 0 to avoid mathematical artifacts.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST process all successfully downloaded subjects from **OpenNeuro ds000224** (HCP Young Adult subset) up to a maximum of **10 subjects** (target n=10 for feasibility within 14GB runner storage), with a hard minimum of 10 valid subjects required to proceed. The system MUST log exclusions for missing or corrupted data. RAM usage per subject processing step MUST be limited to ≤7 GB. (See US-1)
- **FR-002**: The system MUST parcellate the brain using the Schaefer atlas and generate a structural connectivity matrix (streamline count) and functional connectivity matrix (Pearson correlation) for each subject. (See US-1)
- **FR-003**: The system MUST compute degree, betweenness, and eigenvector centrality metrics from the structural matrices and mean absolute functional synchrony from the functional matrices for all ROIs. (See US-2)
- **FR-004**: The system MUST perform a Spearman correlation analysis between each structural centrality metric and functional synchrony across all nodes, treating the design as observational and framing results as associational. (See US-3)
- **FR-005**: The system MUST execute a permutation test with n=1000 random shuffles of the pairings between the centrality vector and the synchrony vector (row permutation) to generate a null distribution and calculate a family-wise error corrected p-value for the observed correlation, based on community standards for permutation testing in connectomics. (See US-3)
- **FR-006**: The system MUST generate a scatter plot visualizing the relationship between structural centrality and functional synchrony, including a regression line, a confidence interval, and annotated statistical values. (See US-3)
- **FR-007**: The system MUST perform a sensitivity analysis sweeping the structural connectivity graph threshold density over a range of low-to-moderate densities and report the stability of the correlation coefficient across these thresholds. (See US-3)

### Key Entities

- **StructuralConnectivityMatrix**: A sparse or dense matrix representing the number of diffusion tractography streamlines between every pair of ROIs in the Schaefer atlas.
- **FunctionalConnectivityMatrix**: A symmetric matrix representing the Pearson correlation coefficients of BOLD time series between every pair of ROIs.
- **CentralityMetrics**: A vector of values (degree, betweenness, eigenvector) associated with each ROI node, derived from the structural matrix.
- **FunctionalSynchrony**: A vector of values representing the mean absolute correlation of each ROI with all other ROIs, derived from the functional matrix.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of successfully processed subjects out of the **target of 10 subjects** is measured against the target of ≥90% (9 subjects) successful processing. (See US-1)
- **SC-002**: The Spearman correlation coefficient (rho) between structural centrality and functional synchrony is measured against the null hypothesis of zero association using a permutation-derived p-value threshold of <0.05. (See US-3)
- **SC-003**: The effect size (Spearman's rho and Fisher's z-transformed 95% confidence interval) is reported for the correlation analysis. (See US-3)
- **SC-004**: The implementation plan MUST demonstrate a runtime estimate < 6 hours on a specified runner type (GitHub Actions free-tier equivalent) to ensure feasibility. (See US-1, US-2, US-3)

## Assumptions

- **Dataset-variable fit**: The **OpenNeuro ds000224** dataset contains both high-quality diffusion MRI (for tractography) and resting-state fMRI (for BOLD time series) for the same subjects. If the specific release lacks a required variable (e.g., specific motion parameters), the system MUST skip that subject and log a warning, proceeding with the remaining valid subjects to maintain a minimum n=10.
- **Inference framing**: Because the study uses observational data without random assignment, all findings regarding the relationship between structural centrality and functional synchrony will be framed strictly as associational, not causal.
- **Multiplicity & power**: The permutation test (n=1000) is assumed to provide sufficient power to detect moderate effect sizes (rho > 0.3) with 400 nodes, given the family-wise error correction is applied to the single primary hypothesis test.
- **Threshold justification & sensitivity**: The structural connectivity graph thresholding uses a fixed density thresholding regime based on community standards for preserving network topology. A sensitivity analysis sweeping the threshold density over a range of values will be performed to ensure the correlation result is robust to this choice.
- **Measurement validity**: The Schaefer atlas is assumed to provide a validated and consistent parcellation scheme that aligns with both the fMRI and dMRI acquisition resolutions.
- **Predictor collinearity**: Degree, betweenness, and eigenvector centrality are known to be correlated; the analysis will report the joint relationship descriptively and include a collinearity diagnostic (VIF) rather than claiming independent predictive effects for each metric in a multivariate model.
- **Compute feasibility**: The analysis design targets a runtime < 6 hours and memory usage < 7 GB on a standard GitHub Actions free-tier runner (ephemeral storage limit 14 GB). The system targets **n=10 subjects** (approx. 4-5 GB raw data + extracted files) to ensure the total I/O stays within the 14 GB storage limit. If storage usage exceeds a predefined capacity threshold during execution, the system MUST halt to prevent job failure.
- **No GPU requirement**: All computations (preprocessing, matrix operations, permutation testing) are performed using CPU-tractable methods (NumPy, SciPy, NetworkX) without requiring CUDA, 8-bit quantization, or GPU accelerators.