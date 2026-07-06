# Feature Specification: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Feature Branch**: `001-neural-correlates-social-exclusion`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does acute simulated social exclusion modulate functional connectivity dynamics within the default mode network (DMN)?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Quality Control (Priority: P1)

The system must successfully download preprocessed fMRI data from OpenNeuro (specifically Cyberball task datasets like ds000030), extract BOLD time-series from canonical DMN regions (PCC, mPFC, angular gyrus) based on event markers for Inclusion and Exclusion conditions, and rigorously filter out subjects with excessive motion artifacts (>3mm displacement) to ensure data integrity.

**Why this priority**: Without a clean, valid dataset, no statistical analysis can be performed. This is the foundational step that determines the feasibility of the entire study.

**Independent Test**: Can be fully tested by executing the data pipeline on a single subject file, verifying the motion parameter output, and confirming the subject is either retained or excluded based on the >3mm threshold.

**Acceptance Scenarios**:

1. **Given** a raw fMRI NIfTI file from OpenNeuro, **When** the motion correction module processes it, **Then** the system outputs a displacement metric and flags the subject as "excluded" if the maximum displacement exceeds 3mm.
2. **Given** a subject with displacement <3mm, **When** the ROI extraction module runs, **Then** the system outputs a time-series matrix for PCC, mPFC, and angular gyrus without errors.

---

### User Story 2 - Connectivity Metric Computation (Priority: P2)

The system must compute Pearson correlation matrices for DMN nodes separately for the **Inclusion** and **Exclusion** conditions (segmented by event markers within the run), and calculate a single "connectivity strength" metric (mean absolute correlation) for each condition per subject.

**Why this priority**: This transforms raw time-series data into the specific quantitative variable (connectivity strength) required to test the research hypothesis.

**Independent Test**: Can be tested by running the calculation on a synthetic time-series dataset with known correlations and verifying the output matches the expected mean absolute correlation value.

**Acceptance Scenarios**:

1. **Given** two time-series vectors (PCC and mPFC) for the Exclusion condition, **When** the correlation module runs, **Then** the system outputs a Pearson correlation coefficient and includes it in the mean absolute correlation calculation.
2. **Given** a subject with both Inclusion and Exclusion time-series, **When** the strength calculator runs, **Then** the system outputs two distinct values: one for Inclusion strength and one for Exclusion strength.

---

### User Story 3 - Statistical Hypothesis Testing (Priority: P3)

The system must execute a non-parametric paired permutation test (iterations adaptive to N) to compare connectivity strength between Inclusion and Exclusion conditions, generating a p-value and effect size, and visualizing the results with 95% confidence intervals.

**Why this priority**: This delivers the final scientific answer to the research question, determining if the observed modulation is statistically significant.

**Independent Test**: Can be tested by running the permutation test on a dataset where the null hypothesis is known to be true (random noise) and verifying the p-value distribution is uniform, or on a dataset with a known shift and verifying significance is detected.

**Acceptance Scenarios**:

1. **Given** paired connectivity strength values (Inclusion vs. Exclusion) for N subjects, **When** the permutation test runs, **Then** the system outputs a p-value and a histogram of the null distribution.
2. **Given** the statistical results, **When** the visualization module runs, **Then** the system generates a bar plot showing the mean difference with error bars representing the 95% confidence interval.

### Edge Cases

- What happens when the downloaded dataset contains fewer subjects than required for a stable permutation test (e.g., N < 10)?
  - **System Behavior**: The system MUST halt execution, return error code `ERR_N_INSUFFICIENT`, and generate a report stating "Insufficient subjects (N < 10) for valid permutation test." (See FR-009).
- How does the system handle a subject where the time-series extraction fails for one specific ROI (e.g., mPFC) but succeeds for others?
  - **System Behavior**: The system MUST exclude the subject from the analysis if any required DMN ROI extraction fails for either condition.
- What occurs if the OpenNeuro API is unavailable or the specific dataset (ds000030) is deprecated/moved?
  - **System Behavior**: The system MUST retry the download a finite number of times with exponential backoff, then fail gracefully with error code `ERR_DATA_UNAVAILABLE`.
- What happens if a subject is missing the Inclusion or Exclusion condition data?
  - **System Behavior**: The system MUST exclude the subject from the paired analysis (See FR-010).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download preprocessed fMRI data from OpenNeuro (e.g., ds000030) and verify file integrity before processing (See US-1).
- **FR-002**: System MUST calculate head motion displacement for every subject and exclude any subject with maximum displacement >3mm (See US-1).
- **FR-003**: System MUST extract BOLD time-series signals from PCC, mPFC, and angular gyrus using a standard atlas (e.g., AAL or Harvard-Oxford) (See US-2).
- **FR-004**: System MUST compute Pearson correlation matrices for DMN nodes separately for the **Inclusion** and **Exclusion** conditions, segmented by event markers within the continuous run (See US-2).
- **FR-005**: System MUST calculate the mean absolute correlation coefficient across all DMN edges to derive a single "connectivity strength" metric per condition (See US-2).
- **FR-006**: System MUST perform a non-parametric paired permutation test comparing connectivity strength between Inclusion and Exclusion conditions. The number of iterations MUST be determined by a bounded function of the subject count to ensure computational feasibility. The permutation MUST be performed at the **subject level** on the derived connectivity strength values (See US-3).
- **FR-007**: System MUST frame all statistical findings as **associational** unless the dataset metadata JSON contains a field `randomization_verified` set to `true`. If `randomization_verified` is false or missing, the output report MUST explicitly use the word "associational" (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (FDR, q ≤ 0.05) if testing more than one specific edge (which is always true for the DMN matrix) (See US-3).
- **FR-009**: System MUST halt execution and return error code `ERR_N_INSUFFICIENT` if the number of valid subjects after QC is less than 10 (See Edge Cases).
- **FR-010**: System MUST verify that each subject has valid time-series data for **both** the Inclusion and Exclusion conditions. Subjects missing either condition MUST be excluded from the paired analysis (See Edge Cases).
- **FR-011**: System MUST perform edge-wise statistical testing for each DMN connection individually, applying FDR correction (q ≤ 0.05) to the resulting p-values, in addition to the global mean metric, to detect opposing effects (See US-3).

### Key Entities

- **Subject**: Represents an individual participant, containing attributes for ID, motion metrics, and condition labels (Inclusion/Exclusion).
- **TimeSeries**: Represents the BOLD signal extracted from a specific ROI for a specific subject and condition.
- **ConnectivityMatrix**: Represents the correlation coefficients between all pairs of DMN nodes for a specific condition.
- **Result**: Represents the outcome of the statistical test, containing p-value, effect size, and confidence intervals.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of subjects retained after motion QC is measured against the total initial download count to verify data quality (See FR-002, US-1).
- **SC-002**: The stability of the connectivity strength metric is measured against the standard deviation of the permutation null distribution (See FR-006, US-3).
- **SC-003**: The validity of the association framing is measured by verifying the output report contains the literal string "associational" when `randomization_verified` is false (See FR-007, US-3).
- **SC-004**: The computational feasibility is measured against a predefined runtime limit. and 7GB RAM constraint on a CPU-only runner (See FR-001, US-1).
- **SC-005**: The sensitivity of the results is measured by successfully generating and reporting a sensitivity curve of p-values across a range of motion thresholds. (See FR-002, US-1).

## Assumptions

- The OpenNeuro dataset `ds000030` (or equivalent Cyberball task dataset) contains preprocessed, motion-corrected fMRI data with clear event markers for "Inclusion" and "Exclusion" conditions within a single continuous run.
- The standard AAL or Harvard-Oxford atlas includes distinct, non-overlapping regions for the PCC, mPFC, and angular gyrus that align with the preprocessed fMRI space.
- The sample size of the downloaded dataset is sufficient (N ≥ 10) to achieve reasonable power for a non-parametric permutation test with adaptive iterations.
- The total size of the required dataset (including time-series extraction intermediates) fits within the disk limit of the GitHub Actions free-tier runner.
- No GPU acceleration is available; all statistical computations must be performed using CPU-optimized libraries (e.g., NumPy, SciPy, scikit-learn).
- The "Inclusion" and "Exclusion" conditions are temporally distinct segments defined by event markers within the same fMRI run, not separate runs.