# Feature Specification: Resting‑State Network Modularity Predicts Social Network Size

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Does higher resting‑state functional network modularity, quantified by the Louvain‐derived modularity quality index (Q), associate with a larger self‑reported social network size in healthy adults?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully retrieve, filter, and preprocess the HCP resting-state fMRI and behavioral data from a large cohort of subjects to produce a clean, subject-level dataset ready for graph analysis.

**Why this priority**: Without a validated, reproducible data pipeline, no analysis can occur. This is the foundational step that ensures data quality and compliance with the CPU-only constraint.

**Independent Test**: The pipeline can be executed end-to-end on a standard CPU-only runner, outputting a single CSV containing subject IDs, preprocessed modularity Q values, and behavioral metrics, with no GPU errors or memory overflows.

**Acceptance Scenarios**:
1. **Given** the HCP S3 bucket is accessible, **When** the pipeline downloads the minimally preprocessed fMRI and behavioral CSVs for 200 randomly selected subjects, **Then** the system successfully filters for subjects with complete behavioral data and valid fMRI runs.
2. **Given** raw fMRI NIfTI files, **When** the system applies band-pass filtering (0.01–0.1 Hz) and regresses out motion parameters and global signal, **Then** the resulting time series are saved without NaN values or dimension mismatches.
3. **Given** the 200-node Schaefer atlas, **When** region-wise time series are extracted, **Then** the system produces a correlation matrix for each subject that is Fisher-z transformed and ready for thresholding.

---

### User Story 2 - Graph Construction and Modularity Calculation (Priority: P2)

The system must construct sparse functional connectivity graphs and compute the Louvain modularity quality index (Q) for each subject.

**Why this priority**: This is the core computational step that generates the primary predictor variable (Q). It directly addresses the research question's "brain-level property" component.

**Independent Test**: The system can compute Q for a cohort of subjects using the specified thresholding method and output a CSV of Q values, verifying that the values fall within the theoretical range for modularity.

**Acceptance Scenarios**:
1. **Given** a Fisher-z transformed correlation matrix, **When** the system thresholds the matrix at the top [deferred] of strongest positive edges, **Then** a sparse, weighted adjacency matrix is generated for each subject.
2. **Given** a set of adjacency matrices, **When** the Louvain algorithm is applied via `python-louvain`, **Then** the system records the modularity quality index Q and the community assignment for each subject.
3. **Given** the computed Q values, **When** the system performs a sanity check, **Then** the distribution of Q values matches expected ranges for resting-state networks (no extreme outliers > 1.0 or < 0.0).

---

### User Story 3 - Statistical Modeling and Association Testing (Priority: P3)

The system must fit a standard linear regression model to test the association between modularity Q and social network size, controlling for relevant covariates.

**Why this priority**: This step answers the research question by quantifying the relationship. It must account for confounding variables to ensure the association is robust.

**Independent Test**: The system executes a regression model and outputs a summary table with coefficients, p-values, and confidence intervals, confirming the procedure correctly calculates the association against the null hypothesis.

**Acceptance Scenarios**:
1. **Given** the dataset of Q values, social network size (friends + acquaintances), and covariates (age, sex, motion, connectivity strength), **When** the system fits a linear regression model with Q as the fixed effect and covariates, **Then** the model outputs a fixed effect coefficient for Q with a p-value and 95% confidence interval.
2. **Given** separate models for "friends" and "acquaintances", **When** the system applies the Benjamini-Hochberg procedure, **Then** the adjusted p-values are reported to control for multiple comparisons.
3. **Given** the primary model results, **When** the system performs a sensitivity analysis by varying the graph threshold across the range defined in SC-002, **Then** the direction and significance of the Q coefficient remain stable.

### Edge Cases

- What happens when a subject's fMRI data contains excessive motion artifacts (framewise displacement > 0.5mm) causing the preprocessing to fail? The system must exclude such subjects and log the exclusion count.
- How does the system handle subjects with missing behavioral data for "number of acquaintances"? The system must impute missing values using the median or exclude the subject from that specific analysis, documenting the decision.
- What if the Louvain algorithm fails to converge for a specific subject's graph? The system must retry with a different random seed up to 3 times, then exclude the subject and log the failure.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download metadata for the full HCP 1200-subject release and a random sample of 200 subjects' resting-state fMRI and behavioral data from the public S3 bucket to ensure CPU feasibility (See US-1).
- **FR-002**: System MUST apply a band-pass filter (low-frequency cutoff to 0.1 Hz) and regress out motion parameters and global signal from the fMRI time series to isolate resting-state fluctuations (See US-1).
- **FR-003**: System MUST extract region-wise time series using the Schaefer cortical atlas and compute Pearson correlation matrices for each subject (See US-1).
- **FR-004**: System MUST construct sparse functional connectivity graphs by thresholding correlation matrices at the top [deferred] of strongest positive edges to ensure comparable density across subjects (See US-2).
- **FR-005**: System MUST compute the Louvain modularity quality index (Q) for each subject's adjacency matrix and store the result (See US-2).
- **FR-006**: System MUST fit a standard linear regression model with Q as the fixed effect, covariates for age, sex, mean framewise displacement, and total connectivity strength (to control for global signal intensity), and report coefficients with robust standard errors (See US-3).
- **FR-007**: System MUST adjust p-values for multiple comparisons using the Benjamini-Hochberg procedure if separate models are run for friends and acquaintances (See US-3).
- **FR-008**: System MUST perform a sensitivity analysis by repeating the primary analysis across the threshold range of 10% to 30% in [deferred] increments to confirm result stability (See US-3).

### Key Entities

- **Subject**: Represents an individual participant, containing attributes: ID, age, sex, mean framewise displacement, social network size (friends, acquaintances), and modularity Q.
- **Graph**: Represents a subject's functional connectivity network, containing attributes: adjacency matrix (sparse), community assignments, and modularity Q.
- **Model**: Represents the statistical analysis output, containing attributes: fixed effect coefficient for Q, p-value, confidence interval, and covariate coefficients.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The association between modularity Q and social network size is measured against the null hypothesis (coefficient = 0) using a standard linear regression model (See FR-006).
- **SC-002**: The stability of the association is measured against the primary result by comparing the coefficient and p-value when the graph threshold is varied from 10% to [deferred] in [deferred] increments (See FR-008).
- **SC-003**: The robustness of the finding is measured against multiple comparisons by ensuring the adjusted p-value (Benjamini-Hochberg) remains significant if separate models are run (See FR-007).
- **SC-004**: The computational feasibility is measured against the GitHub Actions free-tier limits (≤6h runtime, ~7GB RAM) by ensuring the entire pipeline completes within these constraints (See FR-001).
- **SC-005**: The methodological validity is measured by the presence of a sensitivity analysis for the graph threshold, ensuring the result is not an artifact of a single arbitrary cutoff (See FR-008).

## Assumptions

- The HCP 1200-subject release contains the necessary behavioral items ("Number of close friends" and "Number of acquaintances") in the provided CSV files. The pipeline will retrieve the social network size metrics from the HCP behavioral CSVs using the specific columns: `Number of close friends` (representing the inner circle) and `Number of acquaintances` (representing the extended network), as these are the standard HCP data dictionary identifiers for social network size in the 3T behavioral dataset. If these exact column names are missing, the system will attempt to match via case-insensitive substring search for 'friends' and 'acquaintances' before raising a runtime error.
- The Schaefer atlas is compatible with the minimally preprocessed fMRI data in the HCP release without additional registration steps.
- The Louvain algorithm implementation in `python-louvain` is deterministic enough for reproducibility when a fixed random seed is set, or that variability across seeds is negligible for the aggregate result.
- The GitHub Actions free-tier runner provides sufficient disk space for the research to temporarily store the downloaded fMRI data and processed matrices for a representative cohort of subjects..
- The relationship between modularity Q and social network size is assumed to be linear for the purposes of the primary linear regression model; non-linear effects are out of scope for this iteration.
- The analysis is observational; findings will be framed as associational, not causal, as per the study design (no random assignment of brain modularity).
- The sample size of 200 subjects provides adequate statistical power to detect a moderate effect size (r ≈ 0.2) at α = 0.05; power calculations are deferred to the implementation phase but assumed to be feasible.
- The "metabolic cost" of maintaining neural connections, as suggested by the reviewer, is implicitly captured by the "total connectivity strength" covariate; explicit modeling of neural metabolic energy is out of scope for this CPU-limited pipeline.