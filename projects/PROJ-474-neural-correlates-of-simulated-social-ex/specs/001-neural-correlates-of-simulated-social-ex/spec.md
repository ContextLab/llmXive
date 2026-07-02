# Feature Specification: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Feature Branch**: `001-neural-correlates-social-exclusion`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does acute simulated social exclusion modulate functional connectivity dynamics within the default mode network (DMN)?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Quality Control (Priority: P1)

The system must successfully download preprocessed fMRI data from OpenNeuro (specifically Cyberball task datasets like ds000030), extract BOLD time-series from canonical DMN regions (PCC, mPFC, angular gyrus), and rigorously filter out subjects with excessive motion artifacts (>3mm displacement) to ensure data integrity.

**Why this priority**: Without a clean, valid dataset, no statistical analysis can be performed. This is the foundational step that determines the feasibility of the entire study.

**Independent Test**: Can be fully tested by executing the data pipeline on a single subject file, verifying the motion parameter output, and confirming the subject is either retained or excluded based on the >3mm threshold.

**Acceptance Scenarios**:

1. **Given** a raw fMRI NIfTI file from OpenNeuro, **When** the motion correction module processes it, **Then** the system outputs a displacement metric and flags the subject as "excluded" if the maximum displacement exceeds 3mm.
2. **Given** a subject with displacement <3mm, **When** the ROI extraction module runs, **Then** the system outputs a time-series matrix for PCC, mPFC, and angular gyrus without errors.

---

### User Story 2 - Connectivity Metric Computation (Priority: P2)

The system must compute Pearson correlation matrices for DMN nodes separately for pre-task (baseline) and post-exclusion blocks, and calculate a single "connectivity strength" metric (mean absolute correlation) for each condition per subject.

**Why this priority**: This transforms raw time-series data into the specific quantitative variable (connectivity strength) required to test the research hypothesis.

**Independent Test**: Can be tested by running the calculation on a synthetic time-series dataset with known correlations and verifying the output matches the expected mean absolute correlation value.

**Acceptance Scenarios**:

1. **Given** two time-series vectors (PCC and mPFC) for the exclusion block, **When** the correlation module runs, **Then** the system outputs a Pearson correlation coefficient and includes it in the mean absolute correlation calculation.
2. **Given** a subject with both baseline and exclusion time-series, **When** the strength calculator runs, **Then** the system outputs two distinct values: one for baseline strength and one for exclusion strength.

---

### User Story 3 - Statistical Hypothesis Testing (Priority: P3)

The system must execute a non-parametric paired permutation test (10,000 iterations) to compare connectivity strength between inclusion and exclusion conditions, generating a p-value and effect size, and visualizing the results with 95% confidence intervals.

**Why this priority**: This delivers the final scientific answer to the research question, determining if the observed modulation is statistically significant.

**Independent Test**: Can be tested by running the permutation test on a dataset where the null hypothesis is known to be true (random noise) and verifying the p-value distribution is uniform, or on a dataset with a known shift and verifying significance is detected.

**Acceptance Scenarios**:

1. **Given** paired connectivity strength values (baseline vs. exclusion) for N subjects, **When** the permutation test runs with 10,000 iterations, **Then** the system outputs a p-value and a histogram of the null distribution.
2. **Given** the statistical results, **When** the visualization module runs, **Then** the system generates a bar plot showing the mean difference with error bars representing the 95% confidence interval.

### Edge Cases

- What happens when the downloaded dataset contains fewer subjects than required for a stable permutation test (e.g., N < 10)?
- How does the system handle a subject where the time-series extraction fails for one specific ROI (e.g., mPFC) but succeeds for others?
- What occurs if the OpenNeuro API is unavailable or the specific dataset (ds000030) is deprecated/moved?

## Requirements

### Functional Requirements

- **FR-001**: System MUST download preprocessed fMRI data from OpenNeuro (e.g., ds000030) and verify file integrity before processing (See US-1).
- **FR-002**: System MUST calculate head motion displacement for every subject and exclude any subject with maximum displacement >3mm (See US-1).
- **FR-003**: System MUST extract BOLD time-series signals from PCC, mPFC, and angular gyrus using a standard atlas (e.g., AAL or Harvard-Oxford) (See US-2).
- **FR-004**: System MUST compute Pearson correlation matrices for DMN nodes separately for pre-task and post-exclusion blocks (See US-2).
- **FR-005**: System MUST calculate the mean absolute correlation coefficient across all DMN edges to derive a single "connectivity strength" metric per condition (See US-2).
- **FR-006**: System MUST perform a non-parametric paired permutation test with exactly 10,000 iterations to compare connectivity strength between conditions (See US-3).
- **FR-007**: System MUST frame all statistical findings as associational, avoiding causal language unless randomization is explicitly verified in the data metadata (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) if testing more than one specific edge or hypothesis (See US-3).

### Key Entities

- **Subject**: Represents an individual participant, containing attributes for ID, motion metrics, and condition labels (inclusion/exclusion).
- **TimeSeries**: Represents the BOLD signal extracted from a specific ROI for a specific subject and condition.
- **ConnectivityMatrix**: Represents the correlation coefficients between all pairs of DMN nodes for a specific condition.
- **Result**: Represents the outcome of the statistical test, containing p-value, effect size, and confidence intervals.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of subjects retained after motion QC is measured against the total initial download count to verify data quality (See FR-002, US-1).
- **SC-002**: The stability of the connectivity strength metric is measured against the standard deviation of the permutation null distribution (See FR-006, US-3).
- **SC-003**: The validity of the association framing is measured against the study design metadata to ensure no causal claims are made for observational data (See FR-007, US-3).
- **SC-004**: The computational feasibility is measured against the 6-hour runtime limit and 7GB RAM constraint on a CPU-only runner (See FR-001, US-1).
- **SC-005**: The sensitivity of the results is measured by sweeping the motion threshold (e.g., 2.5mm, 3.0mm, 3.5mm) and reporting the variation in the final p-value (See FR-002, US-1).

## Assumptions

- The OpenNeuro dataset `ds000030` (or equivalent Cyberball task dataset) contains preprocessed, motion-corrected fMRI data with clear labels for "inclusion" and "exclusion" blocks.
- The standard AAL or Harvard-Oxford atlas includes distinct, non-overlapping regions for the PCC, mPFC, and angular gyrus that align with the preprocessed fMRI space.
- The sample size of the downloaded dataset is sufficient (N ≥ 15) to achieve reasonable power for a non-parametric permutation test with 10,000 iterations on a CPU-only runner.
- The total size of the required dataset (including time-series extraction intermediates) fits within the 14GB disk limit of the GitHub Actions free-tier runner.
- No GPU acceleration is available; all statistical computations must be performed using CPU-optimized libraries (e.g., NumPy, SciPy, scikit-learn).
- The "post-exclusion" block in the dataset is temporally distinct and separable from the "pre-task" baseline block in the fMRI metadata.
