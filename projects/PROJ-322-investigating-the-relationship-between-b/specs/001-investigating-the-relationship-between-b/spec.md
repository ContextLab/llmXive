# Feature Specification: Investigating the Relationship Between Brain Network Reconfiguration and Recovery from Mild Traumatic Brain Injury

**Feature Branch**: `001-brain-network-reconfiguration`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Reconfiguration and Recovery from Mild Traumatic Brain Injury"

## User Scenarios & Testing

### User Story 1 - Automated Data Acquisition and Preprocessing (Priority: P1)

The system MUST automatically locate, download, and perform minimal preprocessing on longitudinal resting-state fMRI datasets for mTBI patients from OpenNeuro, ensuring data fits within the available RAM constraints.

**Why this priority**: Without valid, preprocessed neuroimaging data, no subsequent analysis or correlation testing can occur. This is the foundational data pipeline step.

**Independent Test**: The system can be tested by running the data ingestion script against a specific OpenNeuro dataset ID; success is confirmed if the script outputs a CSV file listing subject IDs, time points, and file paths to preprocessed NIfTI images, and the total memory footprint during execution never exceeds 6GB.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID containing longitudinal mTBI fMRI data, **When** the ingestion script runs, **Then** the system downloads the data and outputs a manifest CSV with subject IDs and time points, and logs "Memory OK" if peak RAM usage ≤ 6GB.
2. **Given** a dataset with raw (unprocessed) fMRI files, **When** the script detects the raw state, **Then** it applies minimal confound regression using `nilearn` and outputs a processed version, failing immediately if the dataset lacks required time points (acute/chronic).

---

### User Story 2 - Graph Metric Calculation and Correlation Analysis (Priority: P2)

The system MUST compute global efficiency, local efficiency, and modularity (Q) for each subject at each time point, then fit a linear mixed-effects model to test the correlation between these metrics and cognitive recovery scores.

**Why this priority**: This is the core scientific inquiry. It transforms raw data into the statistical evidence required to answer the research question.

**Independent Test**: The system can be tested by running the analysis on a small, synthetic dataset with known correlations; success is confirmed if the output JSON contains the fixed-effect coefficients, p-values, and confidence intervals for the relationship between network metrics and symptom scores.

**Acceptance Scenarios**:

1. **Given** a set of preprocessed connectivity matrices, **When** the analysis script runs, **Then** it outputs a JSON file containing computed values for global efficiency, local efficiency, and modularity for every subject-timepoint pair.
2. **Given** the computed graph metrics and associated cognitive scores, **When** the mixed-effects model is fitted, **Then** the system outputs the correlation coefficient (beta), p-value, and confidence interval for the primary hypothesis.
3. **Given** a model fit that fails to converge, **When** the script detects non-convergence, **Then** it logs a warning, skips the specific subject, and continues processing the remaining batch to ensure robustness.

---

### User Story 3 - Robustness Validation and Sensitivity Reporting (Priority: P3)

The system MUST perform permutation testing (1,000 iterations) to validate significance thresholds and execute a sensitivity analysis on the correlation cutoff to ensure findings are robust to parameter variations.

**Why this priority**: This ensures the scientific validity of the results against small sample sizes and arbitrary threshold choices, addressing methodological soundness requirements.

**Independent Test**: The system can be tested by running the validation module; success is confirmed if the output includes a histogram of the null distribution from permutation testing and a table showing how the correlation coefficient varies across a sweep of threshold values.

**Acceptance Scenarios**:

1. **Given** the primary model results, **When** the permutation test (1,000 iterations) runs, **Then** the system calculates an empirical p-value and reports it alongside the parametric p-value.
2. **Given** a correlation threshold decision, **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over a range of representative values and outputs a table showing the variation in the correlation coefficient for each cutoff.
3. **Given** a total runtime exceeding 5 hours, **When** the job is still running, **Then** the system logs a "Time Limit Warning" and prepares for termination. If runtime exceeds 6 hours, the system MUST halt execution immediately to comply with the constitutional limit.

### Edge Cases

- What happens when the OpenNeuro dataset contains missing time points for specific subjects (e.g., a subject has only acute data)? The system must exclude these subjects from the longitudinal mixed-effects model but include them in cross-sectional checks if applicable, logging the exclusion reason.
- How does the system handle datasets where the AAL atlas parcellation fails due to image quality issues? The system must skip the specific subject, log the error with the subject ID, and continue processing the remaining batch without crashing.
- What happens if the linear mixed-effects model encounters perfect collinearity between graph metrics? The system must detect the Variance Inflation Factor (VIF) > 5, flag the collinearity in the output, and report the joint relationship descriptively rather than claiming independent effects.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess resting-state fMRI data from OpenNeuro for mTBI patients, ensuring the total memory usage remains ≤ 6GB during batch processing (See US-1).
- **FR-002**: System MUST compute global efficiency, local efficiency, and modularity (Q) for each subject using the AAL atlas and `networkx` (See US-2).
- **FR-003**: System MUST fit a linear mixed-effects model with cognitive scores as the dependent variable and graph metrics as fixed effects, including subject ID as a random effect (See US-2).
- **FR-004**: System MUST perform 1,000 iterations of permutation testing to assess the significance of the correlation coefficients (See US-3).
- **FR-005**: System MUST execute a sensitivity analysis sweeping the decision cutoff over a range of representative thresholds and report the variation in the correlation coefficient (See US-3).
- **FR-006**: System MUST detect and report Variance Inflation Factor (VIF) > 5 for predictor collinearity, framing the joint relationship descriptively if detected (See US-2).
- **FR-007**: System MUST validate the correlation findings against an independent functional metric (e.g., Return-to-Work status or a distinct neuropsychological battery) if available; if not available, the system MUST explicitly report this limitation in the final output (See US-2).
- **FR-008**: System MUST apply a proportional sparsity threshold (e.g., 10-20%) to the connectivity matrix before calculating graph metrics to ensure the graph is not fully connected (See US-2).
- **FR-009**: System MUST implement a contingency plan: if the longitudinal sample size (n) is < 20, the system MUST switch to non-parametric bootstrapping for significance testing or report the study as a pilot with appropriate caveats (See US-1).

### Key Entities

- **Subject**: Represents a patient in the mTBI cohort, identified by a unique ID, containing metadata on time points (acute/chronic) and cognitive scores.
- **ConnectivityMatrix**: Represents the Pearson correlation matrix between brain regions (ROIs) for a specific subject at a specific time point.
- **GraphMetrics**: Represents the derived scalar values (global efficiency, local efficiency, modularity) calculated from a ConnectivityMatrix.
- **AnalysisResult**: Represents the statistical output of the mixed-effects model, including coefficients, p-values, and confidence intervals.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation coefficient between network efficiency/modularity and cognitive scores is measured against the null hypothesis (correlation = 0) using the parametric p-value from the mixed-effects model (See US-2).
- **SC-002**: The empirical p-value derived from 1,000 permutation iterations is measured against the parametric p-value to validate robustness (See US-3).
- **SC-003**: The stability of the correlation coefficient across the sensitivity sweep is measured against the baseline coefficient to assess threshold stability (See US-3).
- **SC-004**: The total runtime of the analysis pipeline is measured against the standard CI limit, with a target completion time of ≤ 5 hours to ensure safety margin (See US-1).
- **SC-005**: The peak memory usage during data processing is measured against a limit of ≤ 6GB, with a requirement that no single batch exceeds this limit (See US-1).

## Assumptions

- **Assumption about data availability**: Publicly available OpenNeuro datasets contain the necessary longitudinal time points (acute and chronic) and associated clinical cognitive scores (e.g., Post-Concussion Symptom Scale) for a sample size (n ≥ 20) to perform mixed-effects modeling. If this assumption fails, the contingency plan in FR-009 is activated.
- **Assumption about preprocessing**: Preprocessed fMRI data or data requiring only minimal confound regression (via `nilearn`) is sufficient for graph metric calculation; full pipeline preprocessing (e.g., ICA-AROMA, slice timing correction) is out of scope to fit within CPU/RAM limits.
- **Assumption about atlas compatibility**: The AAL atlas parcellation is compatible with the spatial resolution and preprocessing steps of the downloaded OpenNeuro datasets without requiring additional registration steps.
- **Assumption about statistical power**: The available sample size in public repositories, while potentially small, is sufficient for permutation testing to provide a robust empirical p-value, even if parametric assumptions are weak.
- **Assumption about compute environment**: The GitHub Actions free-tier runner provides consistent access to multiple CPU cores and approximately 7GB RAM without significant noise or throttling that would invalidate the runtime estimate.
- **Assumption about variable fit**: The dataset contains the specific cognitive scores (e.g., PCS) required to match the graph metrics; if a dataset lacks these specific scores, the analysis for that dataset is skipped, and the gap is recorded.