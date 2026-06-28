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

1. **Given** the HCP 1200-subject release is accessible, **When** the download script runs, **Then** resting-state fMRI files and NIH Toolbox Fluid Intelligence scores are retrieved for ≥95% of subjects
2. **Given** raw fMRI data exists, **When** preprocessing completes, **Then** nuisance regression and band-pass filtering (0.01–0.1 Hz) produce preprocessed time series with mean framewise displacement ≤0.2 mm

---

### User Story 2 - Compute Graph Efficiency Metrics (Priority: P2)

The researcher can parcellate brains using the Schaefer atlas with a specified number of regions, compute functional connectivity matrices, and calculate global efficiency and frontoparietal subgraph efficiency metrics for each subject.

**Why this priority**: This delivers the core predictor variables needed for the statistical analysis. P2 because it depends on successfully completed data preprocessing.

**Independent Test**: Can be fully tested by verifying that efficiency metrics are computed for each subject and stored with expected ranges (global efficiency typically 0.1–0.5 for brain networks).

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
- What if the Schaefer atlas parcellation fails for certain subjects? (System MUST skip affected subjects and continue with ≥90% of original cohort)
- How are extreme motion artifacts (>0.5 mm framewise displacement) handled? (System MUST exclude subjects exceeding threshold and log count ≥0)
- What if permutation testing exceeds the 6-hour CPU time limit? (System MUST sample to ≤500 subjects and complete within 6 hours)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data and NIH Toolbox Fluid Intelligence scores from HCP 1200-subject release for ≥95% of subjects (See US-1)
- **FR-002**: System MUST apply nuisance regression and band-pass filtering (0.01–0.1 Hz) with mean framewise displacement ≤0.2 mm (See US-1)
- **FR-003**: System MUST parcellate brains using Schaefer 200-ROI atlas and compute functional connectivity matrices (See US-2)
- **FR-004**: System MUST calculate global efficiency and frontoparietal subgraph efficiency metrics for each subject (See US-2)
- **FR-005**: System MUST perform Pearson/Spearman correlations between efficiency metrics and fluid intelligence scores (See US-3)
- **FR-006**: System MUST apply multiple linear regression with age, sex, and mean framewise displacement as covariates (See US-3)
- **FR-007**: System MUST use 10,000 permutations for family-wise error correction across ≥2 hypothesis tests (See US-3)
- **FR-008**: System MUST frame all findings as associational, not causal, due to observational design (See US-3)
- **FR-009**: System MUST conduct sensitivity analysis on density threshold across {0.15, 0.20, 0.25} and report rate variation (See US-3)
- **FR-010**: System MUST verify NIH Toolbox Fluid Intelligence is a validated instrument with citable validation (See US-3)
- **FR-011**: System MUST compute variance inflation factor (VIF) for predictor collinearity and report VIF ≤5 for all predictors (See US-3)
- **FR-012**: System MUST sample dataset to ≤500 subjects if full 1200-subject analysis exceeds 6-hour CPU limit (See US-3)

### Key Entities *(include if feature involves data)*

- **Subject**: Individual participant with fMRI data and behavioral scores
- **Connectivity Matrix**: Pearson correlation matrix for each subject's brain regions
- **Efficiency Metric**: Graph-theoretical measure (global or frontoparietal) computed per subject
- **Fluid Intelligence Score**: NIH Toolbox behavioral assessment value per subject

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation magnitude between efficiency and intelligence is measured against prior literature expectations (positive associations for global and frontoparietal networks) (See US-3)
- **SC-002**: Family-wise corrected p-value is measured against α=0.05 threshold (See US-3)
- **SC-003**: Sensitivity analysis stability is measured across density thresholds {0.15, 0.20, 0.25} with consistency of effect direction ≥80% (See US-3)
- **SC-004**: Compute time is measured against 6-hour CPU limit on GitHub Actions free-tier (See US-3)
- **SC-005**: Sample size power is measured against ≥80% power for detecting r=0.25 effect at α=0.05 (See US-3)

## Assumptions

- HCP 1200-subject release contains both resting-state fMRI and NIH Toolbox Fluid Intelligence scores for ≥95% of subjects
- Schaefer 200-ROI atlas parcellation is publicly accessible and compatible with HCP data
- All subjects have mean framewise displacement ≤0.5 mm after preprocessing (exclusion threshold)
- GitHub Actions free-tier provides sufficient CPU capacity for 10,000 permutations on sampled dataset
- Fluid intelligence scores are normally distributed or transformations can normalize them
- No GPU acceleration is available; all analysis must complete on CPU within 6 hours
- Dataset size may require sampling to fit within ~7GB RAM constraint
- Frontoparietal network definition follows Yeo-7 atlas parcellation scheme
- Correlation between global and frontoparietal efficiency will be moderate (VIF ≤5)
