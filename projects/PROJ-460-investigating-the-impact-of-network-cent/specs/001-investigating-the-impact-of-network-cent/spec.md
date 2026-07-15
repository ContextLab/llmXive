# Feature Specification: Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder

**Feature Branch**: `001-investigate-asd-centrality`  
**Created**: 2025-01-10  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (US-1)

The system MUST download resting-state fMRI and diffusion MRI (dMRI) data from the ABIDE dataset, preprocess fMRI data using fMRIPrep, and output cleaned time-series data and structural adjacency matrices for each participant.

**Why this priority**: Without reliable, real-world data preprocessing, all downstream analyses (centrality metrics, mediation testing) are invalid. This is the foundational data pipeline that all other functionality depends on.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a sample of participants and verifying output files exist with expected dimensions (timepoints × ROIs for fMRI; streamline counts for dMRI) and that the pipeline completes without timeout on the GitHub Actions runner.

**Acceptance Scenarios**:

1. **Given** valid ABIDE download credentials and participant IDs, **When** the preprocessing pipeline executes on a 2-core runner, **Then** cleaned fMRI time-series files and structural adjacency matrices are produced for the maximum number of participants successfully retrieved, and the job completes within the 6-hour limit.
2. **Given** corrupted or missing fMRI/dMRI data for a participant, **When** the preprocessing pipeline encounters it, **Then** the system logs an error, skips that participant, and continues processing remaining participants without crashing.

### User Story 2 - Centrality Metric Computation and Group Comparison (US-2)

The system MAY compute degree, betweenness, and eigenvector centrality for each brain region from functional connectivity matrices and perform statistical group comparisons between ASD and control groups with FDR correction. This functional analysis is **exploratory** and **not required** for the primary mediation hypothesis; it is performed only if sufficient functional data are available and the researcher opts in. The core scientific analysis (see US-4) focuses on structural centrality mediation.

**Why this priority**: Provides optional exploratory insight into functional network alterations; however, the primary research question concerns structural centrality mediation, so this step is not mandatory.

**Independent Test**: Can be fully tested by running centrality computation on a preprocessed subset of participants and verifying that centrality values are calculated for all 400 ROIs with expected ranges and that statistical outputs include p‑values and q‑values (when the optional step is enabled).

**Acceptance Scenarios**:

1. **Given** preprocessed fMRI data for ≥50 ASD and ≥50 control participants **and** the optional functional analysis flag is enabled, **When** the centrality analysis runs, **Then** centrality metrics (degree, betweenness, eigenvector) are computed for all nodes and FDR‑corrected p‑values are produced.
2. **Given** a specific brain region (e.g., posterior cingulate cortex) **and** the optional functional analysis flag is enabled, **When** the group comparison executes, **Then** the system outputs the mean centrality difference, t‑statistic, and FDR‑corrected q‑value (q < 0.05 threshold), and reports the count of nodes significant at all thresholds and the Jaccard index of the top‑ranked nodes by effect size across thresholds.

### User Story 3 - Diagnostic Classification and Visualization (US-3) *(optional extension)*

The system MAY train a logistic regression classifier on centrality features to assess diagnostic power and generate brain surface visualizations showing centrality differences. This functionality is not required for the primary mediation hypothesis but provides an optional exploratory analysis.

**Why this priority**: This extends the analysis to predictive utility and provides interpretable outputs for scientific communication. While valuable, it builds on US-1 and US-2 functionality and is optional.

**Independent Test**: Can be fully tested by running the classifier on a held‑out test set and verifying that accuracy, AUC, and cross‑validation metrics are reported based on the actual data split.

**Acceptance Scenarios**:

1. **Given** centrality features from ≥50 participants per group, **When** the 5‑fold cross‑validation classifier executes, **Then** diagnostic accuracy, AUC, and confusion matrix are output with 95% confidence intervals calculated from the data.
2. **Given** significant centrality differences at specific ROIs, **When** visualization is requested, **Then** a brain surface figure is generated showing highlighted regions with color‑coded effect sizes derived from the computed statistics.

### User Story 4 - Multimodal Mediation Analysis (US-4) *(core hypothesis)*

The system MUST compute structural network centrality from diffusion‑weighted MRI (dMRI) data and test whether it mediates the relationship between functional connectivity strength and ASD social‑communication severity (e.g., ADOS‑2 CSS). The mediation analysis is a required component of the primary scientific question; if fewer than 30 participants have paired fMRI/dMRI data, the pipeline MUST abort with an explicit error indicating that the primary hypothesis cannot be evaluated.

**Why this priority**: This directly addresses the original scientific hypothesis that structural centrality of DMN hubs mediates the link between functional connectivity and behavioral severity.

**Independent Test**: Can be fully tested on the subset of participants with both fMRI and dMRI by verifying that (a) structural centrality metrics are computed, (b) a mediation model is fitted, and (c) indirect effects are reported with permutation‑based significance.

**Acceptance Scenarios**:

1. **Given** participants with both functional and structural data (≥30), **When** the mediation pipeline runs, **Then** the system reports the indirect effect size, 95% confidence interval, and permutation‑based p‑value.
2. **Given** insufficient structural data (<30 participants), **When** the mediation step is reached, **Then** the system logs “Insufficient structural data for mediation; analysis aborted” and terminates with a non‑zero exit status.

### Edge Cases

- What happens when ABIDE data contains participants with missing diagnosis labels? → System excludes these participants and logs the count.
- How does system handle participants with excessive motion (>3 mm translation)? → System excludes these participants from analysis (see FR-014).
- What happens when the correlation threshold creates a disconnected graph? → System iteratively increases the threshold (15 % → 20 % → 25 %) until connectivity is achieved; if still disconnected, the system calculates centrality on the Largest Connected Component (LCC) and logs the exclusion of isolated nodes (see FR-014).
- What happens when participants with age/sex covariate missing values? → System excludes these participants and reports exclusion count.
- What happens if the ABIDE dataset lacks sufficient participants for the planned power? → The system proceeds with available data, reports the actual sample size, and flags the power limitation in the final output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST target downloading resting-state fMRI data from ABIDE for ≥100 ASD participants and ≥100 control participants; if fewer are available, the system MUST proceed with the maximum number successfully retrieved (See US-1). (See US-1)
- **FR-002**: System MUST download diffusion‑weighted MRI (dMRI) data from ABIDE for participants where both modalities are present; at least 30 participants with paired data are required for mediation analysis (See US-4). (See US-4)
- **FR-003**: System MUST preprocess fMRI data using fMRIPrep Docker container with motion correction, normalization, and nuisance regression (See US-1). (See US-1)
- **FR-004**: System MUST parcellate brain into a set of regions using the Schaefer atlas (Schaefer et al.) (See US-2). (See US-2)
- **FR-005**: System MAY compute degree, betweenness, and eigenvector centrality metrics for each node using NetworkX on functional connectivity matrices for exploratory analysis. The core requirement is structural centrality mediation (See US-4). (See US-2)
- **FR-006**: System MAY perform non‑parametric permutation tests using a max‑t statistic to control family‑wise error rate (FWER) across all nodes, followed by FDR correction (q < 0.05), **if** functional centrality analysis is executed (see FR-005). Permutations MUST be stratified by site and use a fixed random seed. (See US-2). (See US-2)
- **FR-007**: System MAY default to a correlation threshold at the top 15 % of edges to create binary adjacency matrices; the final analysis MUST use results from the sensitivity sweep defined in FR-011 (if functional analysis is performed). (See US-2)
- **FR-008**: System MAY train a logistic regression classifier with k‑fold cross‑validation on centrality features (optional extension) (See US-3). (See US-3)
- **FR-009**: System MUST generate brain surface visualizations using Nilearn showing centrality differences (See US-3). (See US-3)
- **FR-011**: System MAY perform a sensitivity analysis sweeping the correlation threshold over a range of low, moderate, and high values. For each threshold, if the resulting graph is disconnected, the system incrementally raises the threshold to 25 % and then to 30 %; if still disconnected, centrality is computed on the Largest Connected Component (LCC). The analysis reports (a) the count of nodes significant at all thresholds, and (b) the Jaccard index of the top‑ranked nodes by effect size across thresholds. The sparsest threshold that yields a connected graph is used for the primary results **when functional analysis is enabled**. (See US-2)
- **FR-012**: System MUST document collinearity diagnostics for centrality metrics in a file `collinearity_report.txt`. The report shall contain Variance Inflation Factor (VIF) values for degree, betweenness, and eigenvector centrality, and each VIF must be < 5. (See US-2)
- **FR-013**: If ≥30 participants have clinical severity scores (e.g., ADOS‑2 CSS), System MUST correlate the residuals of centrality metrics (after regressing out global functional connectivity strength) with these scores using permutation tests (10,000 permutations) and apply global FDR correction across all 400 ROIs × 3 metrics, reporting the partial correlation coefficient and p‑value calculated from the actual dataset (See US-2). If <30 participants have scores, the system MUST log a warning "Insufficient sample size for robust correlation analysis; proceeding with underpowered analysis" and output the results with a flag indicating underpowered status (See US-2).
- **FR-014**: System MUST exclude participants with motion >3 mm translation or rotation from all analyses and log the exclusion count (See US-1). (See US-1)
- **FR-015**: System MUST increase the correlation threshold as described in FR‑ when graphs are disconnected; if connectivity is still not achieved at [deferred] (the highest allowed threshold), System MUST compute centrality on the LCC, log excluded isolated nodes, and continue (See US-2). (See US-2)
- **FR-016**: System MUST calculate 95 % confidence intervals for accuracy and AUC using 10,000 bootstrap resamples to ensure statistical stability. (See US-3). (See US-3)
- **FR-017**: When structural dMRI data are available, System MUST compute structural centrality and include it in the mediation analysis (See US-4). (See US-4)
- **FR-018**: If classification is performed (see FR‑008), the system MUST apply L1‑regularization (Lasso) with 10‑fold cross‑validation on centrality metrics to handle multicollinearity before classification, ensuring interpretability of feature weights (See US-3). (See US-3)
- **FR-019**: System MUST check for the presence of dMRI data in the ABIDE dataset. If absent, the system MUST log a specific "dMRI_MISSING" flag and proceed with functional‑only analysis, documenting this as a scope boundary (See US‑4). (See US-4)
- **FR-020**: System MUST output a `mediation_analysis_skipped.log` file containing a detailed rationale for skipping mediation analysis due to data absence (See US‑4). (See US-4)
- **FR-021**: System MUST perform mediation analysis testing whether structural centrality mediates the relationship between functional connectivity strength and ASD social‑communication severity, using a bootstrapped indirect‑effect with a sufficient number of resamples to ensure stable estimation. and reporting effect size, 95 % CI, and permutation‑based p‑value derived exclusively from the processed dataset (See US‑4). (See US-4)
- **FR-022**: System MUST verify that at least 30 participants have both fMRI and dMRI data; if fewer are available, the pipeline MUST abort with a clear error message indicating that the primary mediation hypothesis cannot be evaluated (See US‑4). (See US-4)
- **FR-023**: System MUST ensure that all statistical metrics (p‑values, effect sizes, accuracy, AUC) are derived directly from the processed dataset during execution; the system MUST NOT use simulated, hardcoded, or placeholder values for any research results (See US‑2, US‑3). (See US-2, US-3)
- **FR-024**: System MUST frame all findings regarding the relationship between structural centrality, functional connectivity, and behavioral severity as ASSOCIATIONAL, explicitly avoiding causal language unless randomization is present in the study design (See US-4). (See US-4)
- **FR-025**: System MUST perform a power analysis or explicitly report the observed sample size and its implication for statistical power when the number of participants is below 50 per group (See US-2). (See US-2)

### Key Entities *(include if feature involves data)*

- **Participant**: Individual with fMRI scan and diagnosis label (ASD or control), key attributes: age, sex, diagnosis, motion parameters
- **TimeSeries**: Preprocessed fMRI signal for each ROI, attributes: timepoints × parcels (e.g., 400 parcels × 300 timepoints)
- **ConnectivityMatrix**: Pearson correlation matrix between all ROIs, attributes: symmetric matrix with values ∈ [-1, 1]
- **CentralityMetrics**: Network topology measures per node, computed metrics: degree centrality, betweenness centrality, eigenvector centrality
- **StructuralCentralityMetrics**: Network topology measures derived from dMRI tractography (when available)
- **GroupComparison**: Statistical test results between ASD and control, attributes: mean difference, t‑statistic, p‑value, FDR‑corrected q‑value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data‑preprocessing success rate is measured against the requirement that ≥90 % of successfully retrieved participants produce valid output (See US‑1). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-002**: Centrality‑computation completeness is measured against the requirement that all 400 ROIs have centrality values for ≥95 % of participants (See US‑2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-003**: Statistical‑validity is measured against the requirement that permutation‑based FWER correction is applied to all nodes and subsequent FDR correction (q < 0.05) is reported for all tested nodes (See US‑2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-004**: Threshold‑sensitivity is measured against the requirement that sensitivity analysis sweeps correlation threshold over {10 %, 15 %, 20 %} and reports the count of nodes significant at all thresholds and the overlap of top-ranked nodes by effect size (See US‑2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-005**: Classifier‑performance is measured against the baseline of majority‑class accuracy (the accuracy achieved by always predicting the majority class) for binary ASD/control classification, calculated on the held‑out test set only (See US‑3). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-006**: Data‑feasibility is measured against the requirement that the system explicitly logs the availability status of dMRI data (See FR‑019).  
- **SC-007**: Mediation‑analysis significance is measured against the requirement that a bootstrapped indirect effect with 10,000 resamples yields a p‑value ≤ 0.05 (or is reported as non‑significant) and that 95 % confidence intervals are provided (See FR‑021).

## Assumptions

- ABIDE dataset contains the required variables: fMRI time‑series data, diagnosis labels (ASD/control), age, sex, motion parameters, and clinical severity scores (e.g., ADOS) for a variable subset of participants.
- ABIDE also provides diffusion‑weighted MRI (dMRI) data for a subset of participants; at least 30 participants with paired fMRI/dMRI are expected, enabling mediation analysis. **If fewer than 30 paired participants are available, the study cannot address the core hypothesis and will abort (see FR‑022).**
- fMRIPrep Docker container is accessible within GitHub Actions free‑tier environment (CPU‑only, no GPU).
- Schaefer high-resolution atlas is publicly available and compatible with ABIDE preprocessing pipeline.
- The analysis is observational (no random assignment); therefore all findings are framed as ASSOCIATIONAL, not causal.
- Multiple‑comparison correction is required because ≥3 centrality metrics are tested across ≥400 ROIs (total tests >1200).
- The correlation threshold is set to 15 % (top 15 % of edges) as a community‑standard default for binary graph construction in functional connectivity analysis.
- The chosen threshold requires sensitivity analysis; the justification is that this is a standard range in the literature, and sweeping {%, [deferred], [deferred]} tests robustness.
- Sample size/power is determined by available data; the analysis will proceed with available ABIDE participants and report power limitations if sample is <50 per group.
- All methods are CPU‑tractable: NetworkX centrality computation, scikit‑learn logistic regression, and Nilearn visualization run within 6 hours on 2 CPU cores, 7 GB RAM.
- ABIDE data download is permitted under the project's research use license; no commercial use is required.
- Questionnaires/instruments are not used; fMRI‑derived metrics serve as the primary measurements, so instrument validity is established through fMRIPrep preprocessing standards.
- Clinical severity scores (e.g., ADOS‑2) are available for a variable subset of participants; if fewer than 30 participants have scores, the correlation analysis (FR‑013) will be reported as exploratory with appropriate caveats.
- All statistical results (p‑values, effect sizes, accuracy metrics) are computed directly from the processed dataset during execution; no hardcoded, simulated, or placeholder values are inserted into the final results.
