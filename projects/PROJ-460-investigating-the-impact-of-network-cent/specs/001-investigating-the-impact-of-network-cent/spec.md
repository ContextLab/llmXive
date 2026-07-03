# Feature Specification: Investigating Network Centrality in ASD Resting-State fMRI

**Feature Branch**: `001-investigate-asd-centrality`  
**Created**: 2025-01-10  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST download resting-state fMRI data from ABIDE, preprocess it using fMRIPrep, and output cleaned time-series data for each participant.

**Why this priority**: Without reliable preprocessing, all downstream analyses (centrality metrics, group comparisons) are invalid. This is the foundational data pipeline that all other functionality depends on.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a sample of participants and verifying output files exist with expected dimensions (timepoints × ROIs).

**Acceptance Scenarios**:

1. **Given** valid ABIDE download credentials and participant IDs, **When** the preprocessing pipeline executes on a 2-core runner, **Then** cleaned fMRI time-series files are produced for each participant and the job completes without timeout
2. **Given** corrupted or missing fMRI data for a participant, **When** the preprocessing pipeline encounters it, **Then** the system logs an error and skips that participant without crashing

---

### User Story 2 - Centrality Metric Computation and Group Comparison (Priority: P2)

The system MUST compute degree, betweenness, and eigenvector centrality for each brain region, then perform statistical comparisons between ASD and control groups with FDR correction.

**Why this priority**: This is the core scientific analysis answering the research question. Without this, the project cannot produce findings about centrality differences.

**Independent Test**: Can be fully tested by running centrality computation on a preprocessed subset of participants and verifying that centrality values are calculated for all 400 ROIs with expected ranges.

**Acceptance Scenarios**:

1. **Given** preprocessed fMRI data for ≥50 ASD and ≥50 control participants, **When** the centrality analysis runs, **Then** centrality metrics (degree, betweenness, eigenvector) are computed for all nodes and FDR-corrected p-values are produced
2. **Given** a specific brain region (e.g., posterior cingulate cortex), **When** the group comparison executes, **Then** the system outputs the mean centrality difference, t-statistic, and FDR-corrected q-value (q < 0.05 threshold)

---

### User Story 3 - Diagnostic Classification and Visualization (Priority: P3)

The system MUST train a logistic regression classifier on centrality features to assess diagnostic power and generate brain surface visualizations showing centrality differences.

**Why this priority**: This extends the analysis to predictive utility and provides interpretable outputs for scientific communication. While valuable, it builds on P1 and P2 functionality.

**Independent Test**: Can be fully tested by running the classifier on a held-out test set and verifying that accuracy, AUC, and cross-validation metrics are reported.

**Acceptance Scenarios**:

1. **Given** centrality features from ≥50 participants per group, **When** the 5-fold cross-validation classifier executes, **Then** diagnostic accuracy, AUC, and confusion matrix are output with confidence intervals
2. **Given** significant centrality differences at specific ROIs, **When** visualization is requested, **Then** a brain surface figure is generated showing highlighted regions with color-coded effect sizes

---

### Edge Cases

- What happens when ABIDE data contains participants with missing diagnosis labels? → System excludes these participants and logs the count
- How does system handle participants with excessive motion (>3mm translation)? → System flags and excludes these participants from analysis
- What happens when the correlation threshold creates a disconnected graph? → System adjusts threshold to the top percentile of edges as specified, and if still disconnected, logs a warning
- How does system handle participants with age/sex covariate missing values? → System excludes these participants and reports exclusion count

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data from ABIDE for ≥100 ASD participants and ≥100 control participants (See US-1)
- **FR-002**: System MUST preprocess fMRI data using fMRIPrep Docker container with motion correction, normalization, and nuisance regression (See US-1)
- **FR-003**: System MUST parcellate brain into a set of regions using Schaefer atlas with multiple parcels (See US-2)
- **FR-004**: System MUST compute degree, betweenness, and eigenvector centrality metrics for each node using NetworkX (See US-2)
- **FR-005**: System MUST perform two-sample t-tests with FDR correction (q < 0.05) comparing centrality distributions between groups (See US-2)
- **FR-006**: System MUST apply correlation threshold at top-ranked edges to create binary adjacency matrices. (See US-2)
- **FR-007**: System MUST train logistic regression classifier with k-fold cross-validation on centrality features (See US-3)
- **FR-008**: System MUST generate brain surface visualizations using Nilearn showing centrality differences (See US-3)
- **FR-009**: System MUST perform sensitivity analysis sweeping the correlation threshold over a range of representative values and report the count of nodes significant at all thresholds and the Jaccard similarity of significant node sets across thresholds (See US-2)
- **FR-010**: System MUST document collinearity diagnostics for centrality metrics (degree, betweenness, eigenvector) and frame joint relationships descriptively rather than claiming independent effects (See US-2)

### Key Entities *(include if feature involves data)*

- **Participant**: Individual with fMRI scan and diagnosis label (ASD or control), key attributes: age, sex, diagnosis, motion parameters
- **TimeSeries**: Preprocessed fMRI signal for each ROI, attributes: timepoints × parcels (e.g., 400 parcels × 300 timepoints)
- **ConnectivityMatrix**: Pearson correlation matrix between all ROIs, attributes: symmetric matrix with values ∈ [-1, 1]
- **CentralityMetrics**: Network topology measures per node, attributes: degree centrality, betweenness centrality, eigenvector centrality
- **GroupComparison**: Statistical test results between ASD and control, attributes: mean difference, t-statistic, p-value, FDR-corrected q-value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data-preprocessing success rate is measured against the requirement that ≥90% of downloaded participants produce valid output (See US-1)
- **SC-002**: Centrality-computation completeness is measured against the requirement that all 400 ROIs have centrality values for ≥95% of participants (See US-2)
- **SC-003**: Statistical-validity is measured against the requirement that FDR correction is applied and q-values are reported for all tested nodes (See US-2)
- **SC-004**: Threshold-sensitivity is measured against the requirement that sensitivity analysis sweeps correlation threshold over {10%, 15%, 20%} and reports the count of nodes significant at all thresholds and the Jaccard similarity of significant node sets (See US-2)
- **SC-005**: Classifier-performance is measured against the baseline of [deferred] accuracy (or class imbalance ratio if specified) for binary ASD/control classification (See US-3)

## Assumptions

- ABIDE dataset contains the required variables: fMRI time-series data, diagnosis labels (ASD/control), age, sex, and motion parameters for ≥100 participants per group
- fMRIPrep Docker container is accessible within GitHub Actions free-tier environment (CPU-only, no GPU)
- Schaefer multi-parcel atlas is publicly available and compatible with ABIDE preprocessing pipeline
- The analysis is observational (no random assignment); therefore all findings are framed as ASSOCIATIONAL, not causal
- Multiple-comparison correction is required because ≥3 centrality metrics are tested across ≥400 ROIs (total tests >1200)
- The correlation threshold is set to a community-standard default for binary graph construction in functional connectivity analysis.
- The chosen threshold requires sensitivity analysis; the justification is that this is a standard range in the literature, and sweeping {[deferred], [deferred], [deferred]} tests robustness
- Sample size/power is [deferred]; the analysis will proceed with available ABIDE participants and report power limitations if sample is <50 per group
- All methods are CPU-tractable: NetworkX centrality computation, scikit-learn logistic regression, and Nilearn visualization run within 6 hours on 2 CPU cores, 7GB RAM
- ABIDE data download is permitted under the project's research use license; no commercial use is required
- Questionnaires/instruments are not used; fMRI-derived metrics serve as the primary measurements, so instrument validity is established through fMRIPrep preprocessing standards