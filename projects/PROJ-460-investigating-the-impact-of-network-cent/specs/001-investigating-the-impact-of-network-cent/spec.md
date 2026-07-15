# Feature Specification: Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder

**Feature Branch**: `001-investigate-asd-centrality`  
**Created**: 2025-01-10  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST download resting-state fMRI data from ABIDE, preprocess it using fMRIPrep, and output cleaned time-series data for each participant.

**Why this priority**: Without reliable preprocessing, all downstream analyses (centrality metrics, group comparisons) are invalid. This is the foundational data pipeline that all other functionality depends on.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a sample of participants and verifying output files exist with expected dimensions (timepoints × ROIs) and that the pipeline completes without timeout on the GitHub Actions runner.

**Acceptance Scenarios**:

1. **Given** valid ABIDE download credentials and participant IDs, **When** the preprocessing pipeline executes on a 2-core runner, **Then** cleaned fMRI time-series files are produced for the maximum number of participants successfully retrieved (up to the dataset limit), and the job completes within the 6-hour limit.
2. **Given** corrupted or missing fMRI data for a participant, **When** the preprocessing pipeline encounters it, **Then** the system logs an error, skips that participant, and continues processing remaining participants without crashing.

---

### User Story 2 - Centrality Metric Computation and Group Comparison (Priority: P2)

The system MUST compute degree, betweenness, and eigenvector centrality for each brain region, then perform statistical comparisons between ASD and control groups with FDR correction. The analysis is focused on functional centrality because it serves as the mediator in the original hypothesis linking functional connectivity strength to clinical severity. Structural centrality will be incorporated only when dMRI data are available (see User Story 4). **This functional‑only group comparison serves as a necessary preliminary step to characterize baseline differences and to provide effect‑size estimates that inform the subsequent mediation analysis, thereby remaining aligned with the original mediation research question.**

**Why this priority**: This functional‑only comparison is performed to characterize baseline group differences and to provide effect‑size estimates that inform the subsequent mediation analysis; it does not replace the primary mediation hypothesis but supplies necessary intermediate information.

**Independent Test**: Can be fully tested by running centrality computation on a preprocessed subset of participants and verifying that centrality values are calculated for all 400 ROIs with expected ranges and that statistical outputs include p‑values and q‑values.

**Acceptance Scenarios**:

1. **Given** preprocessed fMRI data for ≥50 ASD and ≥50 control participants, **When** the centrality analysis runs, **Then** centrality metrics (degree, betweenness, eigenvector) are computed for all nodes and FDR‑corrected p-values are produced.
2. **Given** a specific brain region (e.g., posterior cingulate cortex), **When** the group comparison executes, **Then** the system outputs the mean centrality difference, t‑statistic, and FDR‑corrected q‑value (q < 0.05 threshold), and reports the count of nodes significant at all thresholds and the Jaccard index of the top‑50 nodes by effect size across thresholds.

---

### User Story 4 - Multimodal Mediation Analysis (Priority: P2)

When diffusion‑weighted MRI (dMRI) data are available for a sufficient number of participants, the system acquires and preprocesses those data, computes structural centrality metrics, and performs a mediation analysis linking structural centrality → functional connectivity strength → ADOS‑2 social‑communication scores.

**Why this priority**: The original scientific hypothesis involves structural hubs mediating functional effects on behavior. Providing a conditional multimodal pathway preserves the core hypothesis when data permit, while gracefully degrading when dMRI data are absent.

**Independent Test**: Can be fully tested by (a) confirming that dMRI data are downloaded for ≥30 participants, (b) verifying that structural connectivity matrices and centrality values are produced, and (c) checking that the mediation analysis outputs indirect‑effect estimates, bootstrap confidence intervals, and a significance flag.

**Acceptance Scenarios**:

1. **Given** ≥30 participants with both fMRI and dMRI, **When** the multimodal pipeline runs, **Then** a mediation report (`mediation_report.md`) is generated containing the indirect effect size, 95% bootstrap CI, and a p‑value (α = 0.05).
2. **Given** insufficient dMRI data, **When** the pipeline reaches the mediation step, **Then** a `mediation_analysis_skipped.log` file is written explaining the data limitation and the study proceeds with functional‑only results.

---

### Edge Cases

- What happens when ABIDE data contains participants with missing diagnosis labels? → System excludes these participants and logs the count.
- How does system handle participants with excessive motion (>3mm translation)? → System excludes these participants from analysis (see FR-012).
- What happens when the correlation threshold creates a disconnected graph? → System iteratively increases the threshold through the set {0.10, 0.15, 0.20} until a connected graph is obtained; if none of these thresholds yield connectivity, the system calculates centrality on the Largest Connected Component (LCC) only, logs the exclusion of isolated nodes, and proceeds with LCC analysis (see FR-013).
- What happens when participants with age/sex covariate missing values? → System excludes these participants and reports exclusion count.
- What happens if the ABIDE dataset lacks sufficient participants for the planned power? → The system proceeds with available data, reports the actual sample size, and flags the power limitation in the final output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST target downloading resting-state fMRI data from ABIDE for ≥100 ASD participants and ≥100 control participants; if fewer are available, the system MUST proceed with the maximum number successfully retrieved (See US-1).
- **FR-002**: System MUST preprocess fMRI data using fMRIPrep Docker container with motion correction, normalization, and nuisance regression (See US-1).
- **FR-003**: System MUST parcellate brain into a set of regions using the Schaefer atlas (Schaefer et al.) (See US-2).
- **FR-004**: System MUST compute degree, betweenness, and eigenvector centrality metrics for each node using NetworkX on functional connectivity matrices. If matched dMRI data are available for ≥30 participants, the system MUST also compute structural centrality metrics (see FR-022) and include them in a mediation analysis (see FR-023). Otherwise, analysis proceeds with functional metrics only. (See US-2, US-4).
- **FR-005**: System MUST perform non‑parametric permutation tests (using 5,000 permutations) using a max‑t procedure with family‑wise error rate (FWER) correction across nodes (no TFCE). FDR correction (q < 0.05) MUST be applied to nodes that survive the FWER gate for ranking. Permutations MUST be stratified by site to account for multi‑site data structure. The system MUST use a fixed random seed of 42 to ensure deterministic reproducibility (See US-2).
- **FR-006**: System MUST default to a correlation threshold at a high percentile of edges to create binary adjacency matrices; the final analysis MUST use results from the sensitivity sweep defined in FR-009 (See US-2).
- **FR-009**: System MUST perform sensitivity analysis sweeping the correlation threshold over a range of low to moderate values. For each threshold that yields a fully connected graph, centrality metrics are computed and node‑wise group comparisons performed. The analysis reports (a) the count of nodes significant at all thresholds considered, and (b) the Jaccard index of the top‑50 nodes by effect size across thresholds. If results conflict across thresholds, the system reports nodes significant at the sparsest *connected* threshold (i.e., the lowest percentage among those that produced a connected graph). Thresholds that produce a disconnected graph are excluded from the sweep. (See US-2, US-4).
- **FR-010**: System MUST generate a collinearity diagnostics report for the three centrality metrics (degree, betweenness, eigenvector). The report includes variance inflation factor (VIF) values for each metric saved as `collinearity_report.csv`. Metrics with VIF > 5 are flagged in the report. A concise summary of the diagnostics is also saved as `collinearity_summary.md`. (See US-2).
- **FR-011**: If ≥30 participants have clinical severity scores (e.g., ADOS‑2 CSS), System MUST correlate the residuals of centrality metrics (after regressing out global functional connectivity strength) with these scores using permutation tests (5,000 permutations) and apply global FDR correction across all 400 ROIs × 3 metrics, reporting the partial correlation coefficient and p‑value calculated from the actual dataset (See US-2). If <30 participants have scores, the system MUST log a warning "Insufficient sample size for robust correlation analysis; proceeding with underpowered analysis" and output the results with a flag indicating underpowered status (See US-2).
- **FR-012**: System MUST exclude participants with motion >3mm translation or rotation from all analyses and log the exclusion count (See US-1).
- **FR-013**: If the graph is disconnected at a given correlation threshold, the system iteratively increases the threshold to the next higher value in the ordered set {0.10, 0.15, 0.20} (representing the top [deferred], [deferred], and [deferred] strongest edges) until a connected graph is obtained. If none of these thresholds yield connectivity, the system calculates centrality metrics on the Largest Connected Component (LCC) only, logs the exclusion of isolated nodes, and proceeds with LCC analysis. (See US-2, US-4).
- **FR-019**: System MUST calculate all statistical metrics (p‑values, effect sizes, accuracy, AUC) directly from the processed dataset during execution; the system MUST NOT use simulated, hardcoded, or placeholder values for any research results (See US-2, US-3).
- **FR-021**: System MUST download diffusion‑weighted MRI (dMRI) data from ABIDE for participants where it is available, and log the number of participants with usable dMRI. (See US-4).
- **FR-022**: System MUST preprocess dMRI data using an appropriate pipeline (e.g., MRtrix3) and compute structural connectivity matrices, then calculate degree, betweenness, and eigenvector centrality for each brain region using the Schaefer atlas. (See US-4).
- **FR-023**: System MUST conduct a mediation analysis using structural centrality as the mediator between functional connectivity strength (average across edges) and ADOS‑2 scores, employing non‑parametric bootstrapping (5,000 resamples) to estimate indirect effects and report significance at α = 0.05. (See US-4).
- **FR-024**: System MUST ensure that all reported quantitative results (e.g., p‑values, effect sizes, accuracy, AUC) are computed directly from the real ABIDE dataset during execution; no simulated, hard‑coded, or placeholder values are used. (See US-1, US-2, US-3, US-4).
- **FR-017**: System MUST check for the presence of dMRI data in the ABIDE dataset. If absent, the system MUST log a specific "dMRI_MISSING" flag and proceed with functional‑only analysis, documenting this as a scope boundary (See US-2).
- **FR-018**: System MUST output a `mediation_analysis_skipped.log` file containing a detailed rationale for skipping mediation analysis due to data absence (See US-2).

### Key Entities *(include if feature involves data)*

- **Participant**: Individual with fMRI scan and diagnosis label (ASD or control), key attributes: age, sex, diagnosis, motion parameters
- **TimeSeries**: Preprocessed fMRI signal for each ROI, attributes: timepoints × parcels (e.g., 400 parcels × 300 timepoints)
- **ConnectivityMatrix**: Pearson correlation matrix between all ROIs, attributes: symmetric matrix with values ∈ [-1, 1]
- **CentralityMetrics**: Network topology measures per node, computed metrics: degree centrality, betweenness centrality, eigenvector centrality
- **GroupComparison**: Statistical test results between ASD and control, attributes: mean difference, t‑statistic, p‑value, FDR‑corrected q‑value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data-preprocessing success rate is measured against the requirement that ≥90% of successfully retrieved participants produce valid output (See US-1). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-002**: Centrality-computation completeness is measured against the requirement that all 400 ROIs have centrality values for ≥95% of participants (See US-2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-003**: Statistical-validity is measured against the requirement that FDR correction is applied and q-values are reported for all tested nodes (See US-2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-004**: Threshold-sensitivity is measured against the requirement that sensitivity analysis sweeps correlation threshold over {0.10, 0.15, 0.20} and reports the count of nodes significant at all thresholds and the overlap of top‑50 nodes by effect size (See US-2, US-4). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-005**: Classifier-performance is measured against the baseline of majority-class accuracy (the accuracy achieved by always predicting the majority class) for binary ASD/control classification, calculated on the held‑out test set only (See US-3). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-006**: Data-feasibility is measured against the requirement that the system explicitly logs the availability status of dMRI data (See FR-017) (See US-4). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-007**: dMRI availability logging compliance is measured against the requirement that the system reports the number of participants with usable dMRI (See FR-021) and the presence/absence flag (See FR-017). (See US-4).

## Assumptions

- ABIDE dataset contains the required variables: fMRI time-series data, diagnosis labels (ASD/control), age, sex, motion parameters, and clinical severity scores (e.g., ADOS‑2) for a variable subset of participants.
- fMRIPrep Docker container is accessible within GitHub Actions free‑tier environment (CPU‑only, no GPU).
- Schaefer 400‑parcel atlas is publicly available and compatible with ABIDE preprocessing pipeline.
- The analysis is observational (no random assignment); therefore all findings are framed as ASSOCIATIONAL, not causal.
- Multiple‑comparison correction is required because ≥3 centrality metrics are tested across ≥400 ROIs (total tests >1200).
- The correlation threshold is set to 15% (top 15% of edges) as a default starting point, a community‑standard default for binary graph construction in functional connectivity analysis. The chosen threshold requires sensitivity analysis; the justification is that this is a standard range in the literature, and sweeping {0.10, 0.15, 0.20} tests robustness.
- Sample size/power is determined by available data; the analysis will proceed with available ABIDE participants and report power limitations if sample is <50 per group.
- All methods are CPU‑tractable: NetworkX centrality computation, scikit‑learn logistic regression, and Nilearn visualization run within 6 hours on 2 CPU cores, 7 GB RAM.
- ABIDE data download is permitted under the project's research use license; no commercial use is required.
- Questionnaires/instruments are not used; fMRI‑derived metrics serve as the primary measurements, so instrument validity is established through fMRIPrep preprocessing standards.
- Clinical severity scores (e.g., ADOS‑2) are available for a variable subset of participants; if fewer than 30 participants have scores, the correlation analysis (FR-011) will be reported as exploratory with appropriate caveats.
- All statistical results (p‑values, effect sizes, accuracy metrics) are computed directly from the processed dataset during execution; no hardcoded, simulated, or placeholder values are inserted into the final results.
