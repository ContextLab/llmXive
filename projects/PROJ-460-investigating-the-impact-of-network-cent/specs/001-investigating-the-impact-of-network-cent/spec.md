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

The system MUST compute degree, betweenness, and eigenvector centrality for each brain region, then perform statistical comparisons between ASD and control groups with FDR correction. The scope is strictly limited to functional connectivity group comparisons due to the absence of structural connectivity (dMRI) data in the ABIDE dataset; the original multimodal mediation hypothesis is not tested.

**Why this priority**: This is the core scientific analysis answering the research question within the available data constraints. Without this, the project cannot produce findings about centrality differences.

**Independent Test**: Can be fully tested by running centrality computation on a preprocessed subset of participants and verifying that centrality values are calculated for all 400 ROIs with expected ranges and that statistical outputs include p-values and q-values.

**Acceptance Scenarios**:

1. **Given** preprocessed fMRI data for ≥50 ASD and ≥50 control participants, **When** the centrality analysis runs, **Then** centrality metrics (degree, betweenness, eigenvector) are computed for all nodes and FDR-corrected p-values are produced.
2. **Given** a specific brain region (e.g., posterior cingulate cortex), **When** the group comparison executes, **Then** the system outputs the mean centrality difference, t-statistic, and FDR-corrected q-value (q < 0.05 threshold), and reports the count of nodes significant at all thresholds and the Jaccard index of the top-50 nodes by effect size across thresholds.

---

### User Story 3 - Diagnostic Classification and Visualization (Priority: P3)

The system MUST train a logistic regression classifier on centrality features to assess diagnostic power and generate brain surface visualizations showing centrality differences.

**Why this priority**: This extends the analysis to predictive utility and provides interpretable outputs for scientific communication. While valuable, it builds on P1 and P2 functionality.

**Independent Test**: Can be fully tested by running the classifier on a held-out test set and verifying that accuracy, AUC, and cross-validation metrics are reported based on the actual data split.

**Acceptance Scenarios**:

1. **Given** centrality features from ≥50 participants per group, **When** the 5-fold cross-validation classifier executes, **Then** diagnostic accuracy, AUC, and confusion matrix are output with 95% confidence intervals calculated from the data.
2. **Given** significant centrality differences at specific ROIs, **When** visualization is requested, **Then** a brain surface figure is generated showing highlighted regions with color-coded effect sizes derived from the computed statistics.

---

### Edge Cases

- What happens when ABIDE data contains participants with missing diagnosis labels? → System excludes these participants and logs the count.
- How does system handle participants with excessive motion (>3mm translation)? → System excludes these participants from analysis (see FR-012).
- What happens when the correlation threshold creates a disconnected graph? → System iteratively increases the threshold (15% → 20% → 25% → 30%) until connectivity is achieved; if still disconnected at [deferred], the system calculates centrality on the Largest Connected Component (LCC) and logs the exclusion of isolated nodes (see FR-013).
- What happens when participants with age/sex covariate missing values? → System excludes these participants and reports exclusion count.
- What happens if the ABIDE dataset lacks sufficient participants for the planned power? → The system proceeds with available data, reports the actual sample size, and flags the power limitation in the final output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST target downloading resting-state fMRI data from ABIDE for ≥100 ASD participants and ≥100 control participants; if fewer are available, the system MUST proceed with the maximum number successfully retrieved (See US-1).
- **FR-002**: System MUST preprocess fMRI data using fMRIPrep Docker container with motion correction, normalization, and nuisance regression (See US-1).
- **FR-003**: System MUST parcellate brain into a set of regions using the Schaefer atlas (Schaefer et al., 2018) (See US-2).
- **FR-004**: System MUST compute degree, betweenness, and eigenvector centrality metrics for each node using NetworkX on functional connectivity matrices. The scope is strictly limited to functional connectivity group comparisons; the multimodal mediation analysis is not performed due to data absence (See US-2).
- **FR-005**: System MUST perform non-parametric permutation tests (10,000 permutations) using a max-t procedure with cluster-based FWER correction (via Threshold-Free Cluster Enhancement, TFCE) as the primary gate to identify significant clusters. FDR correction (q < 0.05) MUST be applied ONLY to the nodes within those surviving clusters for ranking. Permutations MUST be stratified by site to account for multi-site data structure. The system MUST use a fixed random seed of 42 to ensure deterministic reproducibility (See US-2).
- **FR-006**: System MUST default to a correlation threshold at the top 15% of edges to create binary adjacency matrices; the final analysis MUST use results from the sensitivity sweep defined in FR-009 (See US-2).
- **FR-007**: System MUST train logistic regression classifier with k-fold cross-validation on centrality features (See US-3).
- **FR-008**: System MUST generate brain surface visualizations using Nilearn showing centrality differences (See US-3).
- **FR-009**: System MUST perform sensitivity analysis sweeping the correlation threshold over {10%, 15%, 20%} and report the count of nodes significant at all thresholds and the overlap (Jaccard index) of the top-50 nodes by effect size across thresholds. If results conflict, the system MUST report only nodes significant at the sparsest threshold (10%) that yields a connected graph. If the [deferred] graph is disconnected, the system MUST skip to the next threshold in the set {15%, 20%} until a connected graph is found (See US-2).
- **FR-010**: System MUST document collinearity diagnostics for centrality metrics (degree, betweenness, eigenvector) and frame joint relationships descriptively rather than claiming independent effects (See US-2).
- **FR-011**: If ≥30 participants have clinical severity scores (e.g., ADOS-2 CSS), System MUST correlate the residuals of centrality metrics (after regressing out global functional connectivity strength) with these scores using permutation tests (10,000 permutations) and apply global FDR correction across all 400 ROIs × 3 metrics, reporting the partial correlation coefficient and p-value calculated from the actual dataset (See US-2). If <30 participants have scores, the system MUST log a warning "Insufficient sample size for robust correlation analysis; proceeding with underpowered analysis" and output the results with a flag indicating underpowered status (See US-2).
- **FR-012**: System MUST exclude participants with motion >3mm translation or rotation from all analyses and log the exclusion count (See US-1).
- **FR-013**: If the graph is disconnected at the default threshold (15%), System MUST iteratively increase the threshold to the top 20%, 25%, and [deferred] of edges until connectivity is achieved. If still disconnected at [deferred], the system MUST calculate centrality metrics on the Largest Connected Component (LCC) only, log the exclusion of isolated nodes, and proceed with the LCC analysis (See US-2).
- **FR-014**: System MUST calculate 95% confidence intervals for accuracy and AUC using 5,000 bootstrap resamples to ensure statistical stability. (See US-3).
- **FR-015**: The multimodal mediation analysis is not performed due to the absence of matched dMRI data in ABIDE. The scope is strictly limited to functional connectivity group comparisons. This limitation is documented as a scope boundary, not a failure of the analysis pipeline (See US-2).
- **FR-016**: System MUST apply L1-regularization (Lasso) with 10-fold cross-validation on centrality metrics to handle multicollinearity before classification, ensuring interpretability of feature weights (See US-2).
- **FR-017**: System MUST check for the presence of dMRI data in the ABIDE dataset. If absent, the system MUST log a specific "dMRI_MISSING" flag and proceed with functional-only analysis, documenting this as a scope boundary (See US-2).
- **FR-018**: System MUST output a `mediation_analysis_skipped.log` file containing a detailed rationale for skipping mediation analysis due to data absence (See US-2).
- **FR-019**: System MUST calculate all statistical metrics (p-values, effect sizes, accuracy, AUC) directly from the processed dataset during execution; the system MUST NOT use simulated, hardcoded, or placeholder values for any research results (See US-2, US-3).

### Key Entities *(include if feature involves data)*

- **Participant**: Individual with fMRI scan and diagnosis label (ASD or control), key attributes: age, sex, diagnosis, motion parameters
- **TimeSeries**: Preprocessed fMRI signal for each ROI, attributes: timepoints × parcels (e.g., 400 parcels × 300 timepoints)
- **ConnectivityMatrix**: Pearson correlation matrix between all ROIs, attributes: symmetric matrix with values ∈ [-1, 1]
- **CentralityMetrics**: Network topology measures per node, computed metrics: degree centrality, betweenness centrality, eigenvector centrality
- **GroupComparison**: Statistical test results between ASD and control, attributes: mean difference, t-statistic, p-value, FDR-corrected q-value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data-preprocessing success rate is measured against the requirement that ≥90% of successfully retrieved participants produce valid output (See US-1). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-002**: Centrality-computation completeness is measured against the requirement that all 400 ROIs have centrality values for ≥95% of participants (See US-2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-003**: Statistical-validity is measured against the requirement that FDR correction is applied and q-values are reported for all tested nodes (See US-2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-004**: Threshold-sensitivity is measured against the requirement that sensitivity analysis sweeps correlation threshold over {10%, 15%, 20%} and reports the count of nodes significant at all thresholds and the overlap of top-50 nodes by effect size (See US-2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-005**: Classifier-performance is measured against the baseline of majority-class accuracy (the accuracy achieved by always predicting the majority class) for binary ASD/control classification, calculated on the held-out test set only (See US-3). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-006**: Data-feasibility is measured against the requirement that the system explicitly logs the availability status of dMRI data (See FR-017).

## Assumptions

- ABIDE dataset contains the required variables: fMRI time-series data, diagnosis labels (ASD/control), age, sex, motion parameters, and clinical severity scores (e.g., ADOS-2) for a variable subset of participants.
- fMRIPrep Docker container is accessible within GitHub Actions free-tier environment (CPU-only, no GPU).
- Schaefer 400-parcel atlas is publicly available and compatible with ABIDE preprocessing pipeline.
- The analysis is observational (no random assignment); therefore all findings are framed as ASSOCIATIONAL, not causal.
- Multiple-comparison correction is required because ≥3 centrality metrics are tested across ≥400 ROIs (total tests >1200).
- The correlation threshold is set to 15% (top 15% of edges) as a default starting point, a community-standard default for binary graph construction in functional connectivity analysis.
- The chosen threshold requires sensitivity analysis; the justification is that this is a standard range in the literature, and sweeping {[deferred], [deferred], [deferred]} tests robustness.
- Sample size/power is determined by available data; the analysis will proceed with available ABIDE participants and report power limitations if sample is <50 per group.
- All methods are CPU-tractable: NetworkX centrality computation, scikit-learn logistic regression, and Nilearn visualization run within 6 hours on 2 CPU cores, 7GB RAM.
- ABIDE data download is permitted under the project's research use license; no commercial use is required.
- Questionnaires/instruments are not used; fMRI-derived metrics serve as the primary measurements, so instrument validity is established through fMRIPrep preprocessing standards.
- Clinical severity scores (e.g., ADOS-2) are available for a variable subset of participants; if fewer than 30 participants have scores, the correlation analysis (FR-011) will be reported as exploratory with appropriate caveats.
- All statistical results (p-values, effect sizes, accuracy metrics) are computed directly from the processed dataset during execution; no hardcoded, simulated, or placeholder values are inserted into the final results.