# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Anticipatory Reward Processing

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Anticipatory Reward Processing using HCP data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system MUST download and prepare a subsample of subjects from the Human Connectome Project (HCP) dataset, including both resting-state and task-based fMRI data, ensuring all data fits within the RAM and disk constraints of the free-tier GitHub Actions runner.

**Why this priority**: Without valid, preprocessed data, no analysis can occur. This is the foundational step that enables all subsequent research questions to be tested.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script and verifying the output directory contains exactly 50 subject folders OR fewer if valid subjects are skipped per Edge Case logic, with both resting-state and task-fMRI NIfTI files, and that the total disk usage is ≤ 14 GB.

**Acceptance Scenarios**:

1. **Given** the HCP data access credentials are valid, **When** the ingestion script runs, **Then** data for a cohort of unique subjects is downloaded and stored in the designated local directory.
2. **Given** the downloaded data, **When** the preprocessing step executes, **Then** BOLD time series are extracted for the Power 264 atlas nodes (excluding ventral striatum) and the ventral striatum ROI, resulting in cleaned CSV files for each subject.
3. **Given** the total dataset size, **When** the script checks system resources, **Then** the memory footprint of the loaded data remains within acceptable system limits at any point during processing.

---

### User Story 2 - Dynamic Connectivity and Flexibility Calculation (Priority: P2)

The system MUST compute dynamic functional connectivity (dFC) metrics for each subject's resting-state data using a sliding window approach and derive a "flexibility" score representing the frequency of state switching. The state space is defined by K-means clustering (K=4) with K-means++ initialization and a fixed random seed to ensure determinism.

**Why this priority**: This step operationalizes the predictor variable (network flexibility) required to test the research hypothesis. It transforms raw time series into a quantifiable metric.

**Independent Test**: The calculation can be tested independently by running the dFC module on a small synthetic dataset with known switching patterns and verifying the flexibility score correlates with the known ground truth and produces identical results on repeated runs (due to fixed seed).

**Acceptance Scenarios**:

1. **Given** a subject's resting-state BOLD time series, **When** the sliding window analysis runs (window size = 30 TRs, step = 1 TR), **Then** a sequence of functional connectivity states is generated for each time point using K-means (K=4, seed=42).
2. **Given** the sequence of states, **When** the flexibility metric is calculated, **Then** a single scalar value representing the state switching frequency is output for the subject.
3. **Given** the calculated flexibility scores, **When** the system validates the output, **Then** all valid subjects have a non-null flexibility score.

---

### User Story 3 - Correlation Analysis and Significance Testing (Priority: P3)

The system MUST correlate individual flexibility scores with ventral striatum activation magnitudes during reward anticipation and perform permutation testing to establish statistical significance.

**Why this priority**: This step directly answers the research question. It synthesizes the predictor and outcome variables to produce the final empirical result.

**Independent Test**: The analysis can be tested independently by providing a mock dataset with a known correlation coefficient and verifying the Pearson correlation calculation and permutation p-value match the expected values.

**Acceptance Scenarios**:

1. **Given** the flexibility scores and ventral striatum activation values for 50 subjects, **When** the Pearson correlation is computed, **Then** a correlation coefficient (r) and raw p-value are returned.
2. **Given** the observed correlation, **When** the permutation test runs (A sufficient number of iterations will be performed to ensure convergence of the optimization process.), **Then** an empirical p-value is calculated based on the null distribution of shuffled correlations.
3. **Given** the results, **When** the system generates the report, **Then** the output includes the correlation coefficient, the empirical p-value, and a plot of the correlation with the regression line.

### Edge Cases

- What happens when a subject's resting-state data is missing or corrupted? (System MUST skip that subject and log a warning, proceeding with the remaining valid subjects).
- What happens when the total available pool of subjects with both scan types is less than 50? (System MUST fail fast with an error message indicating insufficient data and terminate execution).
- How does the system handle a subject with zero variance in their flexibility score (constant state)? (System MUST flag this subject as an outlier and exclude them from the correlation analysis to avoid division by zero or undefined statistics).
- How does the system handle a case where the permutation test p-value equals exactly 0? (System MUST report p < 1/1001 rather than 0 to reflect the finite number of permutations).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and subset HCP resting-state and task-fMRI data for exactly 50 subjects to ensure memory constraints are met (See US-1).
- **FR-002**: System MUST extract BOLD time series from the Power 264 atlas nodes (excluding any nodes overlapping with the ventral striatum ROI) and the ventral striatum ROI for all valid subjects (See US-1).
- **FR-003**: System MUST compute dynamic functional connectivity using a sliding window approach (window size = 30 TRs, step = 1 TR) to derive flexibility metrics (See US-2).
- **FR-003a**: System MUST define the state space for flexibility calculation using K-means clustering with K=4 states, K-means++ initialization, and a fixed random seed of 42 to ensure deterministic results (See US-2).
- **FR-004**: System MUST calculate a single scalar "flexibility score" representing the state switching frequency for each subject (See US-2).
- **FR-005**: System MUST perform a Pearson correlation analysis between flexibility scores and ventral striatum activation magnitudes (See US-3).
- **FR-006**: System MUST execute a permutation test with 1,000 iterations to determine the statistical significance of the correlation (See US-3).
- **FR-007**: System MUST ensure the final markdown report contains the exact phrase "associational relationship" and does not contain the word "causal" in the results interpretation section (See US-3).
- **FR-008**: System MUST validate that the resting-state and task-fMRI data for each subject originate from distinct session IDs in the HCP metadata; if any subject's sessions match, the system MUST exclude that subject and log a warning (See US-1).
- **FR-009**: System MUST perform a sensitivity analysis by repeating the correlation calculation for sliding window sizes of, 30, and 40 TRs, and report the resulting correlation coefficients and p-values for each window size in the final output (See US-2).
- **FR-010**: System MUST terminate execution with a non-zero exit code and a clear error message if the total number of valid subjects with both scan types is less than 50 (See Edge Cases).

### Key Entities

- **Subject**: Represents an individual participant in the HCP dataset, identified by a unique ID, containing both resting-state and task-fMRI data.
- **Flexibility Score**: A scalar metric derived from resting-state dFC, representing the frequency of state transitions per unit time, calculated using K-means (K=4, seed=42).
- **Reward Activation**: A scalar metric representing the mean BOLD signal change in the ventral striatum during reward cue epochs.
- **Correlation Result**: The output object containing the Pearson coefficient, empirical p-value, and confidence intervals.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The total memory usage during data processing is measured against the 7 GB RAM constraint of the free-tier runner (See FR-001).
- **SC-002**: The statistical significance of the correlation is measured against the null distribution generated by 1,000 permutations (See FR-006).
- **SC-003**: The robustness of the flexibility metric is measured by the system reporting the variation in correlation coefficients and p-values across sliding window sizes {20, 30, 40} TRs (See FR-009).
- **SC-004**: The validity of the dataset-variable fit is measured by confirming the presence of both resting-state and task-fMRI data for all 50 subjects (See FR-001).
- **SC-005**: The data integrity regarding session independence is measured by the percentage of subjects (target [deferred]) that pass the distinct session ID validation check (See FR-008).

## Assumptions

- **Assumption about data availability**: The HCP dataset provides minimally preprocessed resting-state and task-fMRI data for at least 50 subjects with both scan types available and distinct session IDs. If fewer than 50 are available, the system will fail as per FR-010.
- **Assumption about methodological validity**: The Power 264 atlas is an appropriate and validated node definition for calculating dynamic functional connectivity in this context, provided the ventral striatum nodes are excluded to prevent double-dipping.
- **Assumption about computational limits**: The sliding window approach with a sufficient number of permutation iterations will complete within the -hour time limit of the GitHub Actions free-tier runner on a 50-subject sample.
- **Assumption about variable fit**: The ventral striatum ROI can be reliably extracted from the standard MNI space coordinates provided by the task paradigm without requiring subject-specific anatomical segmentation.
- **Assumption about inference**: Since the study design is observational (no random assignment), the results will be interpreted strictly as associations between resting-state dynamics and task-evoked responses. The temporal separation of scans ensures data independence, but the correlation test assumes statistical independence of observations (subjects).