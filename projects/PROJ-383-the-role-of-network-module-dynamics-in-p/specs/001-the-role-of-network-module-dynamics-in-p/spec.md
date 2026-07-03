# Feature Specification: The Role of Network Module Dynamics in Predicting Individual Differences in Working Memory Capacity

**Feature Branch**: `001-network-module-dynamics-wm`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Research on temporal flexibility of resting-state functional network modules predicting working memory capacity using HCP data."

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

**User Journey**: As a researcher, I need to download and preprocess a subset of resting-state fMRI data and behavioral scores from the Human Connectome Project (HCP) so that I can perform correlation analysis without exceeding local CPU/RAM constraints.

**Why this priority**: This is the foundational step. Without valid, cleaned data that fits the compute environment, no analysis can proceed. It addresses the "Dataset-variable fit" and "Compute feasibility" constraints immediately.

**Independent Test**: The script successfully downloads a sample of subjects, loads the preprocessed fMRI time series and 2-back accuracy scores into memory, and outputs a consolidated CSV/Parquet file without crashing or exceeding memory limits.

**Acceptance Scenarios**:
1. **Given** a valid HCP dataset ID (ds000224), **When** the ingestion script runs with a limit of 100 subjects, **Then** the system outputs a single data file containing time-series matrices and behavioral scores for exactly 100 subjects.
2. **Given** the downloaded data, **When** the system checks memory usage during loading (measured via `psutil` peak RSS), **Then** peak RAM usage remains ≤ 7 GB and the process completes within 30 minutes.
3. **Given** missing behavioral scores for a subject, **When** the ingestion script runs, **Then** that subject is excluded from the dataset and a log entry records the exclusion reason.

---

### User Story 2 - Dynamic Flexibility Metric Computation (Priority: P2)

**User Journey**: As a researcher, I need to compute the "temporal flexibility" metric for each subject by applying sliding-window community detection so that I have a quantitative predictor variable representing network reconfiguration.

**Why this priority**: This implements the core scientific hypothesis (the "X" in "X predicts Y"). It transforms raw time-series data into the specific metric required for the study.

**Independent Test**: The pipeline processes the loaded time-series data, applies the sliding window and Louvain algorithm, and outputs a single flexibility score per subject.

**Acceptance Scenarios**:
1. **Given** a subject's preprocessed fMRI time series, **When** the sliding window (fixed length, fixed step) and Louvain algorithm are applied, **Then** a community assignment sequence is generated for every time window.
2. **Given** the community assignment sequence, **When** the flexibility metric is calculated, **Then** the output is a scalar value representing the average probability of node switching across the whole brain.
3. **Given** the computed flexibility scores for all 100 subjects, **When** the system validates the output, **Then** all scores are within the theoretical range [0, 1] and no NaN values are present.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**User Journey**: As a researcher, I need to perform a correlation analysis between flexibility scores and working memory capacity, including a permutation test for significance and sensitivity analysis, so that I can determine if the relationship is statistically robust.

**Why this priority**: This delivers the final scientific result. It addresses the "Inference framing", "Multiplicity", and "Robustness" requirements by ensuring the statistical claim is valid, corrected, and stable across parameter choices.

**Independent Test**: The analysis script runs the correlation test, permutation test, and sensitivity analysis, outputting a correlation coefficient, p-value, and a report indicating significance status and stability.

**Acceptance Scenarios**:
1. **Given** the flexibility scores and working memory scores, **When** a partial Spearman correlation is computed controlling for mean FD, **Then** the system outputs a partial correlation coefficient (rho) and a raw p-value.
2. **Given** the observed partial correlation, **When** a non-parametric permutation test (exactly 1,000 permutations) is run, **Then** the system outputs a corrected p-value and a histogram of the null distribution.
3. **Given** the results, **When** the report is generated, **Then** it explicitly states whether the finding is "associational" (not causal), includes the sensitivity analysis for window length, and confirms motion control was applied.

### Edge Cases

- **What happens when** the sliding window size results in an insufficient number of time points for community detection? (System must skip the subject or flag an error).
- **How does the system handle** subjects with excessive motion artifacts that correlate with both flexibility and memory scores? (System MUST apply a motion scrubbing strategy: exclude subjects with mean FD > 0.2mm, and for included subjects, remove time points with FD > 0.2mm).
- **What happens when** the permutation test yields a p-value of exactly 0 or 1 due to discrete sampling? (System must apply a standard correction, e.g., p = 1/(N+1)).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess resting-state fMRI time series and n-back behavioral scores for a subset of subjects from the HCP (ds000224) dataset, ensuring total memory usage does not exceed a predefined threshold during execution. (See US-1)
- **FR-002**: System MUST compute time-varying functional connectivity matrices using a sliding window approach with a primary window length of 60 seconds and a step size of 10 seconds, and MUST be capable of iterating through window lengths of {30s, 60s, 90s} for sensitivity analysis. (See US-2)
- **FR-003**: System MUST apply the Louvain community detection algorithm with a resolution parameter set to a standard value and run 100 iterations with consensus clustering on each windowed connectivity matrix to identify network modules for every subject. (See US-2)
- **FR-004**: System MUST calculate the "flexibility" metric as the probability of node community switching across windows and average this value across the whole brain to produce a single predictor score per subject. (See US-2)
- **FR-005**: System MUST perform a partial Spearman correlation test between the whole-brain flexibility metric and working memory capacity scores, controlling for mean Framewise Displacement (FD) to account for motion artifacts. (See US-3)
- **FR-006**: System MUST run a non-parametric permutation test with exactly 1,000 permutations on the partial correlation statistic to establish a null distribution and determine robustness against the null hypothesis. (See US-3)
- **FR-007**: System MUST frame all reported statistical findings as "associational" rather than causal in the final report, given the observational nature of the data. (See US-3)
- **FR-008**: System MUST apply a motion scrubbing strategy where subjects with mean Framewise Displacement (FD) > 0.2mm are excluded from analysis, and for all included subjects, the system MUST regress out 6 rigid-body motion parameters, their temporal derivatives, and the mean FD value using Ordinary Least Squares (OLS), and MUST remove (scrub) any individual time points where FD > 0.2mm. (See US-3)
- **FR-009**: System MUST perform a sensitivity analysis on the sliding window length by repeating the primary analysis with window lengths of 30s, 60s, and 90s, and report the stability of the p-value across these configurations, defined as a max absolute difference between p-values < 0.05. (See US-3)
- **FR-010**: System MUST measure peak memory usage via `psutil` peak RSS to verify the ≤ 7 GB constraint during the ingestion and processing phases. (See US-1)

### Key Entities

- **Subject**: An individual participant from the HCP dataset, identified by a unique ID.
- **TimeSeries**: A matrix of fMRI signal intensity over time for a specific subject.
- **FlexibilityScore**: A scalar value (0 to 1) representing the temporal flexibility of network modules for a subject.
- **WorkingMemoryScore**: A scalar value representing the accuracy (e.g., d-prime or percent correct) on the 2-back task for a subject.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The partial correlation coefficient (rho) between flexibility and working memory capacity (controlling for mean FD) is measured against the null hypothesis of rho=0 with a significance threshold of alpha = 0.05 to determine statistical significance. (See US-3)
- **SC-002**: The p-value from the permutation test is measured against the standard alpha threshold of 0.05 to determine if the association is robust against the null hypothesis. (See US-3)
- **SC-003**: The sensitivity analysis of the window length is measured against the stability of the p-value across a sweep of window lengths {30s, 60s, 90s} to ensure result reliability, defined as a max absolute difference between p-values < 0.05. (See US-3)
- **SC-004**: The memory footprint of the pipeline is measured against a constrained RAM capacity of 7 GB during the processing of the 100-subject subset (measured via `psutil` peak RSS). (See US-1)
- **SC-005**: The dataset-variable fit is measured by verifying that the HCP ds000224 release contains both the required resting-state fMRI time series and the 2-back behavioral scores for the same subjects. (See US-1)

## Assumptions

- **Assumption about data source**: The Human Connectome Project (OpenNeuro ds000224) contains preprocessed resting-state fMRI data and corresponding 2-back task behavioral scores for the same set of subjects, and the data is accessible via the OpenNeuro API without authentication barriers that would block CI execution.
- **Assumption about compute environment**: The analysis will run on a GitHub Actions free-tier runner (limited CPU cores, ~7 GB RAM) without GPU acceleration; therefore, all algorithms must be CPU-tractable and memory-efficient. No CUDA or mixed-precision operations are used.
- **Assumption about methodology**: The Louvain algorithm is an appropriate and standard method for community detection in this context, and a window length of 60 seconds is sufficient to capture relevant dynamic reconfigurations without introducing excessive noise, provided consensus clustering is used.
- **Assumption about inference**: Since the study uses observational data without random assignment, any significant correlation will be interpreted strictly as an association, not a causal effect of flexibility on memory.
- **Assumption about sample size**: A sample size of 100 subjects is a feasibility limit imposed by the compute environment (7GB RAM) for an exploratory analysis; this is not a statistical power justification, and larger samples would be preferred for definitive confirmation.
- **Assumption about motion artifacts**: The Human Connectome Project (HCP) data contains sufficient motion parameters (6 rigid-body parameters and derivatives) and Framewise Displacement (FD) estimates to allow for the implementation of a volume scrubbing strategy (removing high-FD volumes) and mean FD regression as specified in FR-008.
- **Assumption about collinearity**: The flexibility metric and working memory score are not definitionally derived from one another, and no other predictors in the model are definitionally bounded by the flexibility metric, avoiding inherent collinearity issues in the correlation analysis.