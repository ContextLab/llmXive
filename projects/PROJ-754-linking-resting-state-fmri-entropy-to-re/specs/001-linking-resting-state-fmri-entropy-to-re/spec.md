# Feature Specification: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Feature Branch**: `001-resting-state-entropy-risk`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition & Preprocessing Pipeline (Priority: P1)

The system MUST download HCP resting-state fMRI parcellated time series and Domain-Specific Risk-Taking (DSRT) scores for a defined subject cohort, and filter high-motion subjects to ensure data quality suitable for entropy computation.

**Why this priority**: Without clean, accessible neuroimaging and behavioral data, no subsequent analysis can occur. This is the foundational dependency for all other features.

**Independent Test**: Can be fully tested by verifying the download of a subset of 200 subjects (to fit CI constraints) and confirming the exclusion of subjects with mean framewise displacement (FD) ≥ 0.2mm.

**Acceptance Scenarios**:

1. **Given** valid HCP S3 credentials, **When** the pipeline executes, **Then** it downloads minimally preprocessed 4mm parcellated time series and DSRT scores.
2. **Given** a subject with mean FD ≥ 0.2mm, **When** the quality control step runs, **Then** that subject is excluded from the analysis cohort.

---

### User Story 2 - Multiscale Entropy Computation (Priority: P2)

The system MUST compute multiscale sample entropy (mSE) for each cortical parcel across the valid subject cohort, averaging across scales m=1–5 to derive a single entropy metric per parcel per subject.

**Why this priority**: This implements the core predictor variable (neural entropy) required to test the research hypothesis. It relies on the data from US-1 but is a distinct computational step.

**Independent Test**: Can be fully tested by running the entropy computation on a small test dataset (e.g., 5 subjects) and verifying the output shape matches (subjects × parcels).

**Acceptance Scenarios**:

1. **Given** preprocessed time series for a subject, **When** mSE is computed with parameters m=1–5, **Then** a single averaged entropy value is produced for each parcel.
2. **Given** a parcel with insufficient timepoints, **When** the computation runs, **Then** the system flags the parcel as invalid rather than crashing.

---

### User Story 3 - Statistical Modeling & Reporting (Priority: P3)

The system MUST fit a separate linear regression model per cortical parcel predicting DSRT scores from parcel entropy, perform permutation-based family-wise error correction using the max-statistic method, and generate a summary report including parcel-wise association maps.

**Why this priority**: This delivers the final scientific result (the hypothesis test) and is dependent on the outputs of US-1 and US-2.

**Independent Test**: Can be fully tested by running the statistical model on the computed entropy data and verifying the output includes a PDF report and a NIfTI map of significant parcels.

**Acceptance Scenarios**:

1. **Given** entropy values and DSRT scores, **When** the mass-univariate models fit (one per parcel), **Then** it produces β-coefficients for each parcel with p-values corrected for multiple comparisons using the max-statistic null distribution.
2. **Given** the analysis is observational, **When** the report is generated, **Then** it explicitly frames findings as associational rather than causal.

---

### Edge Cases

- What happens when HCP credentials are missing or invalid? The system MUST fail gracefully with a clear error message and not attempt to download partial data.
- How does system handle subjects with missing DSRT scores? The system MUST exclude these subjects from the analysis and log the exclusion count.
- What happens if the permutation test exceeds the 6-hour CI limit? The system MUST abort and report a timeout error rather than producing incomplete results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download HCP minimally preprocessed 4mm parcellated time series and DSRT scores for a subset of N=200 subjects to ensure fit within 14GB disk constraint. (See US-1)
- **FR-002**: System MUST exclude any subject with mean framewise displacement (FD) ≥ 0.2mm, a standard motion threshold for rs-fMRI quality control. (See US-1)
- **FR-003**: System MUST compute multiscale sample entropy (m=1–5) for every cortical parcel and average across scales. (See US-2)
- **FR-004**: System MUST fit a separate linear regression model per cortical parcel with parcel entropy as predictor and DSRT score as outcome, controlling for age, sex, and motion. (See US-3)
- **FR-005**: System MUST perform 5,000 label-shuffled permutations, re-computing the full statistical map for each permutation to build a null distribution of the maximum statistic for family-wise error (FWE) correction at p < 0.05. (See US-3)
- **FR-006**: System MUST frame all statistical findings as associational, not causal, given the observational nature of the data. (See US-3)
- **FR-007**: System MUST run on CPU-only hardware without requiring GPU acceleration. (See US-3)
- **FR-008**: System MUST include a sensitivity analysis sweeping entropy tolerance parameter r over {0.1, 0.15, 0.2} to report variation in the number of significant parcels and variation in effect size estimates. (See US-3)
- **FR-009**: System MUST validate that the entropy metric is not trivially correlated with residual noise variance by including a noise-variance covariate or performing a partial correlation analysis. (See US-2)

### Key Entities

- **Subject**: An individual participant with associated fMRI time series and DSRT score.
- **Parcel**: A cortical region of interest (e.g., Schaefer 400) with associated entropy value.
- **Entropy Metric**: A scalar value representing multiscale sample entropy for a specific parcel.
- **Risk Score**: A scalar value representing the DSRT score for a specific subject.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Total pipeline execution time is measured against the 6-hour GitHub Actions free-tier limit. (See US-1)
- **SC-002**: Peak memory usage is measured against the 7GB RAM constraint during entropy computation and model fitting. (See US-2)
- **SC-003**: Output completeness is measured against the requirement for a parcel-wise association map and PDF report. (See US-3)
- **SC-004**: Sensitivity analysis coverage is measured against the requirement to report rate variation across r ∈ {0.1, 0.15, 0.2}. (See US-3)
- **SC-005**: Collinearity diagnostics (Variance Inflation Factor) are measured against a threshold of VIF < 5 for covariates. (See US-3)
- **SC-006**: Statistical power is measured against a target of Power ≥ 0.80 to detect effect size d=0.3, calculated via simulation or analytical approximation. (See US-3)
- **SC-007**: Permutation testing runtime is measured against the 6-hour CI limit for 5,000 iterations with N=200 subjects. (See US-3)

## Assumptions

- HCP provides minimally preprocessed 4mm parcellated time series that fit within the 14GB disk constraint when downloading a subset of 200 subjects; full cohort (N=1200) requires larger storage.
- DSRT scores are available in the HCP behavioral dataset for all subjects in the selected subset.
- The analysis is observational; any statistical association does not imply causal direction between neural entropy and risk-taking.
- The `pyEntropy` package and `statsmodels` library are available in the CI environment without GPU dependencies.
- Motion threshold FD < 0.2mm is sufficient to exclude excessive motion artifacts for this analysis.
- Entropy tolerance parameter r = 0.15 is the community-standard default for multiscale sample entropy in fMRI, consistent with Richiardi et al., 2011.