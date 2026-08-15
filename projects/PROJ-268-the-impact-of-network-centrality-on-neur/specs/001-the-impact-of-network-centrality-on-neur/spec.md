# Feature Specification: The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

**Feature Branch**: `001-impact-of-network-centrality-on-neural-synchrony`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Do structural-connectivity-derived centrality metrics (from diffusion MRI) predict the magnitude of functional synchrony measured from resting-state fMRI?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

**Description**: The researcher MUST be able to download a subset of HCP Young Adult data (n=50), preprocess fMRI BOLD time series and diffusion MRI tractography, and generate a parcellated structural and functional connectivity matrix for each subject using the Schaefer 400 atlas.

**Why this priority**: Without clean, matched structural and functional data matrices, no analysis can occur. This is the foundational data preparation step required for all subsequent statistical testing.

**Independent Test**: The pipeline can be fully tested by verifying that for a single subject, the script outputs a valid structural adjacency matrix (200x200 or 400x400) and a functional correlation matrix of the same dimensions, with no missing values due to preprocessing failures.

**Acceptance Scenarios**:
1. **Given** raw HCP data for a subject, **When** the preprocessing script runs, **Then** it outputs a clean structural connectivity matrix and a functional connectivity matrix in the project's `data/processed` directory.
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
1. **Given** the computed centrality and synchrony vectors, **When** the analysis script runs, **Then** it outputs a JSON report containing the Spearman rho, p-value (uncorrected and permutation-corrected), and Cohen's d effect size.
2. **Given** the statistical results, **When** the visualization module runs, **Then** it generates a high-resolution PNG scatter plot with the regression line, 95% confidence interval, and a text annotation of the p-value.

---

### Edge Cases

- **What happens when** the HCP download fails or a subject file is corrupted? The pipeline MUST skip the corrupted subject, log a warning, and proceed with the remaining valid subjects (minimum n=10 required to proceed).
- **How does the system handle** a structural matrix where the number of nodes does not match the functional matrix (e.g., due to atlas mismatch)? The system MUST halt execution with a clear error message identifying the dimension mismatch before attempting any correlation.
- **What happens when** the permutation test p-value is exactly 0 (all permutations yield a lower correlation)? The system MUST report p < 1/1000 (0.001) rather than 0 to avoid mathematical artifacts.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and preprocess resting-state fMRI and diffusion MRI data for at least 50 subjects from the HCP Young Adult release, limiting total RAM usage to ≤7 GB per subject processing step. (See US-1)
- **FR-002**: The system MUST parcellate the brain using the Schaefer 400 atlas and generate a structural connectivity matrix (streamline count) and functional connectivity matrix (Pearson correlation) for each subject. (See US-1)
- **FR-003**: The system MUST compute degree, betweenness, and eigenvector centrality metrics from the structural matrices and mean absolute functional synchrony from the functional matrices for all 400 ROIs. (See US-2)
- **FR-004**: The system MUST perform a Spearman correlation analysis between each structural centrality metric and functional synchrony across all nodes, treating the design as observational and framing results as associational. (See US-3)
- **FR-005**: The system MUST execute a permutation test with n=1000 random node label shuffles to generate a null distribution and calculate a family-wise error corrected p-value for the observed correlation. (See US-3)
- **FR-006**: The system MUST generate a scatter plot visualizing the relationship between structural centrality and functional synchrony, including a regression line, 95% confidence interval, and annotated statistical values. (See US-3)

### Key Entities

- **StructuralConnectivityMatrix**: A sparse or dense matrix representing the number of diffusion tractography streamlines between every pair of ROIs in the Schaefer atlas.
- **FunctionalConnectivityMatrix**: A symmetric matrix representing the Pearson correlation coefficients of BOLD time series between every pair of ROIs.
- **CentralityMetrics**: A vector of values (degree, betweenness, eigenvector) associated with each ROI node, derived from the structural matrix.
- **FunctionalSynchrony**: A vector of values representing the mean absolute correlation of each ROI with all other ROIs, derived from the functional matrix.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of successfully processed subjects (out of the requested 50) is measured against the target of ≥90% (45 subjects) to ensure sufficient statistical power. (See US-1)
- **SC-002**: The Spearman correlation coefficient (rho) between structural centrality and functional synchrony is measured against the null hypothesis of zero association using a permutation-derived p-value threshold of <0.05. (See US-3)
- **SC-003**: The effect size (Cohen's d) of the correlation is measured against the target of ≥0.5 to demonstrate practical relevance beyond statistical significance. (See US-3)
- **SC-004**: The computational runtime for the full analysis (preprocessing + analysis + visualization) is measured against the constraint of ≤6 hours on a standard GitHub Actions free-tier runner (2 CPU, 7 GB RAM). (See US-1, US-2, US-3)

## Assumptions

- **Dataset-variable fit**: The HCP Young Adult 1200 Subjects release contains both high-quality diffusion MRI (for tractography) and resting-state fMRI (for BOLD time series) for the same subjects. If the specific release lacks a required variable (e.g., specific motion parameters), `[NEEDS CLARIFICATION: does the HCP 1200 release contain the exact motion parameter files required for the fMRIPrep-lite nuisance regression?]`.
- **Inference framing**: Because the study uses observational data without random assignment, all findings regarding the relationship between structural centrality and functional synchrony will be framed strictly as associational, not causal.
- **Multiplicity & power**: The permutation test (n=1000) is assumed to provide sufficient power to detect moderate effect sizes (rho > 0.3) with 400 nodes, given the family-wise error correction is applied to the single primary hypothesis test.
- **Threshold justification & sensitivity**: The structural connectivity graph thresholding (if applied) uses a fixed density based on community standards. for preserving network topology. A sensitivity analysis sweeping the threshold density over a range of values will be performed to ensure the correlation result is robust to this choice.
- **Measurement validity**: The Schaefer 400 atlas is assumed to provide a validated and consistent parcellation scheme that aligns with both the fMRI and dMRI acquisition resolutions.
- **Predictor collinearity**: Degree, betweenness, and eigenvector centrality are known to be correlated; the analysis will report the joint relationship descriptively and include a collinearity diagnostic (VIF) rather than claiming independent predictive effects for each metric in a multivariate model.
- **Compute feasibility**: The analysis assumes that processing a cohort of subjects with a 400-node atlas will fit within the 7 GB RAM and 6-hour time limit. of the GitHub Actions free tier; if memory usage exceeds limits, the sample size will be reduced to n=20 to maintain feasibility.
- **No GPU requirement**: All computations (preprocessing, matrix operations, permutation testing) are performed using CPU-tractable methods (NumPy, SciPy, NetworkX) without requiring CUDA, 8-bit quantization, or GPU accelerators.
