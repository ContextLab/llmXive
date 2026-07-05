# Feature Specification: Brain Network Efficiency and Fluid Intelligence

**Feature Branch**: `001-brain-network-efficiency-fluid-intelligence`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Efficiency and Fluid Intelligence"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Preprocess HCP Data (Priority: P1)

The researcher can download resting-state fMRI data and fluid intelligence scores from the HCP large-scale release, preprocess the data with nuisance regression and band-pass filtering, and prepare it for graph analysis.

**Why this priority**: This is the foundational step—without data acquisition and preprocessing, no analysis can proceed. P1 because the entire research question depends on having properly preprocessed data.

**Independent Test**: Can be fully tested by verifying that the downloaded and preprocessed data files exist with expected dimensions and quality metrics.

**Acceptance Scenarios**:

1. **Given** the Human Connectome Project (HCP) large-scale subject release is accessible, **When** the download script runs, **Then** resting-state fMRI files and NIH Toolbox Fluid Intelligence scores are retrieved for ≥95% of subjects
2. **Given** raw fMRI data exists, **When** preprocessing completes, **Then** nuisance regression and band-pass filtering (0.01–0.1 Hz) produce preprocessed time series with mean framewise displacement ≤0.2 mm

---

### User Story 2 - Compute Graph Efficiency Metrics (Priority: P2)

The researcher can parcellate brains using the Schaefer atlas with a specified number of regions, compute functional connectivity matrices, and calculate global efficiency and frontoparietal subgraph efficiency metrics for each subject.

**Why this priority**: This delivers the core predictor variables needed for the statistical analysis. P2 because it depends on successfully completed data preprocessing.

**Independent Test**: Can be fully tested by verifying that efficiency metrics are computed for each subject and stored with expected ranges (global efficiency for brain networks).

**Acceptance Scenarios**:

1. **Given** preprocessed fMRI time series exist, **When** graph metrics are computed, **Then** global efficiency and frontoparietal efficiency values are generated for ≥95% of subjects
2. **Given** connectivity matrices are thresholded at 20% density, **When** binary graphs are created, **Then** all graphs maintain comparable sparsity with edge density within ±1% of target

---

### User Story 3 - Statistical Analysis and Results Reporting (Priority: P3)

The researcher can run correlation analyses and multiple regression models, apply permutation testing for family-wise error correction, and generate results that document the relationship between efficiency metrics and fluid intelligence.

**Why this priority**: This delivers the final scientific output. P3 because it depends on both data preprocessing and metric computation being complete.

**Independent Test**: Can be fully tested by verifying that statistical outputs include correlation coefficients, p-values, and effect sizes for both global and frontoparietal efficiency.

**Acceptance Scenarios**:

1. **Given** efficiency metrics and intelligence scores exist, **When** correlation analysis runs, **Then** Pearson/Spearman correlations are computed with family-wise corrected p-values from a large number of permutations
2. **Given** multiple regression models are fit, **When** results are generated, **Then** models include age, sex, and mean framewise displacement as covariates with effect sizes reported

---

### Edge Cases

- What happens when HCP data access is restricted or unavailable? (System MUST fail gracefully with ≥1 retry attempt before halting)
- How does the system handle subjects with missing fluid intelligence scores? (System MUST exclude subjects with missing scores and log count ≥0)
- What if the Schaefer atlas parcellation fails for certain subjects? (System MUST skip affected subjects and continue with ≥95% of original cohort)
- How are extreme motion artifacts (>0.5 mm framewise displacement) handled? (System MUST exclude subjects exceeding threshold and log count ≥0)
- What if permutation testing exceeds the -hour CPU time limit? (System MUST sample to ≤500 subjects and complete within 6 hours)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data and NIH Toolbox Fluid Intelligence scores from HCP large-scale release

The specific value to remove/generalize: 'large-scale'

Rewritten passage:
This study addresses the research question of how large-scale multimodal neuroimaging data can enhance the understanding of brain-behavior relationships. We will employ a method of cross-subject pattern analysis and connectivity mapping to identify consistent neural signatures. Key references include the foundational work by Van Essen et al. (2013) regarding the Human Connectome Project framework. for ≥95% of subjects (See US-1)
- **FR-002**: System MUST apply nuisance regression and band-pass filtering (0.01–0.1 Hz) with mean framewise displacement ≤0.2 mm (See US-1)
- **FR-003**: System MUST parcellate brains using the Schaefer 200-ROI atlas, compute functional connectivity matrices retaining only positive edges, and calculate global and frontoparietal efficiency (See US-2)
- **FR-004**: System MUST calculate global efficiency and frontoparietal subgraph efficiency metrics for each subject (See US-2)
- **FR-005**: System MUST perform Pearson/Spearman correlations between efficiency metrics and fluid intelligence scores (See US-3)
- **FR-006**: System MUST apply multiple linear regression with age, sex, and mean framewise displacement as covariates (See US-3)
- **FR-007**: System MUST use up to 10,000 permutations to generate a null distribution of the max statistic for family-wise error correction across the 2 primary hypothesis tests (See US-3)
- **FR-008**: System MUST frame all findings as associational, not causal, due to observational design (See US-3)
- **FR-009**: System MUST compute variance inflation factor (VIF) for predictor collinearity; if VIF > 5, the system MUST flag the collinearity and report results from an orthogonalized model or ridge regression (See US-3)
- **FR-010**: System MUST include a citation to a validation study for the NIH Toolbox Fluid Intelligence score (See US-3)
- **FR-011**: System MUST sample dataset to ≤500 subjects only if the 6-hour CPU limit is exceeded; this is a hard cap to ensure time-bounded execution (See US-3)
- **FR-012**: System MUST repeat efficiency computation using the Schaefer high-resolution ROI atlas

References: Schaefer et al. (2018)
Research Question: How does atlas resolution impact the efficiency of network computation?
Method: Comparative analysis of efficiency metrics across varying ROI parcellations. and report comparison metrics as a robustness check (See US-2)
- **FR-013**: System MUST compute weighted-graph efficiency as a robustness check alongside binary graph metrics (See US-3)
- **FR-014**: System MUST document that the frontoparietal subgraph is defined by the Yeo-7 atlas (task-independent) to avoid circular definition bias (See US-3)

### Key Entities *(include if feature involves data)*

- **Subject**: Individual participant with fMRI data and behavioral scores
- **Connectivity Matrix**: Pearson correlation matrix for each subject's brain regions (positive edges only)
- **Efficiency Metric**: Graph-theoretical measure (global or frontoparietal) computed per subject
- **Fluid Intelligence Score**: NIH Toolbox behavioral assessment value per subject

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation magnitude (r) is computed and reported; results are compared against prior literature (e.g., r > 0.1) (See US-3)
- **SC-002**: Family-wise corrected p-value is measured against α=0.05 threshold (See US-3)
- **SC-003**: Robustness check stability is measured by comparing effect direction consistency across parcellation resolutions (200-ROI, 400-ROI) with a target of ≥80% consistency (See US-3)
- **SC-004**: Compute time is measured against a standard CPU time limit on GitHub Actions free-tier. (See US-3)
- **SC-005**: Sample size power is measured against ≥80% power for detecting r=0.25 effect at α=0.05 (See US-3)

## Assumptions

- HCP 1200-subject release contains both resting-state fMRI and NIH Toolbox Fluid Intelligence scores for ≥95% of subjects
- Schaefer 200-ROI atlas parcellation is publicly accessible and compatible with HCP data
- Schaefer 400-ROI atlas parcellation is publicly accessible and compatible with HCP data
- All subjects have mean framewise displacement ≤0.5 mm after preprocessing (exclusion threshold)
- GitHub Actions free-tier provides sufficient CPU capacity for 10,000 permutations on sampled dataset
- Fluid intelligence scores are normally distributed or transformations can normalize them
- No GPU acceleration is available; all analysis must complete on CPU within 6 hours
- Dataset size may require sampling to fit within available RAM constraints.
- Frontoparietal network definition follows Yeo-7 atlas parcellation scheme
- Correlation between global and frontoparietal efficiency will be moderate (VIF ≤5) unless remediation is triggered