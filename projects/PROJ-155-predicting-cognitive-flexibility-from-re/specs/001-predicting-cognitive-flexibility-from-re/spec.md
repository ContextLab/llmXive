# Feature Specification: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Feature Branch**: `001-predict-cognitive-flexibility-rsfc-variability`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does inter‑individual variability in resting‑state functional connectivity (RSFC) predict performance on cognitive‑flexibility tasks?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system MUST successfully download the HCP 1200-subject release (resting-state fMRI and behavioral data), apply the HCP minimal preprocessing outputs, and parcellate the data using the Schaefer atlas with a high-resolution parcellation scheme (Schaefer et al., 2018) to generate a clean, analysis-ready dataset.

**Why this priority**: Without a valid, preprocessed dataset containing both the neural predictors (RSFC) and the behavioral outcome (NIH Toolbox scores), no analysis can occur. This is the foundational data layer for the entire research question.

**Independent Test**: The pipeline can be tested by running the download and preprocessing scripts on a subset of 5 subjects and verifying that the output CSV contains exactly the following columns with the specified data types: `Subject_ID` (string), `Mean_FD` (float), `Age` (integer), `Sex` (string), and `Flexibility_Score` (float). The test MUST fail if any column is missing, contains null values, or has an incorrect type.

**Acceptance Scenarios**:

1. **Given** a valid HCP data download link and credentials, **When** the ingestion script runs, **Then** the script downloads the resting-state fMRI and behavioral files for the target subjects and places them in the designated working directory without data corruption.
2. **Given** raw fMRI NIfTI files, **When** the parcellation step executes using the Schaefer 200 atlas, **Then** the output is a 4D NIfTI file or time-series matrix where each voxel is mapped to exactly one of the 200 regions, and no regions are missing.
3. **Given** the behavioral data file, **When** it is merged with the neuroimaging data, **Then** the resulting dataset contains exactly one row per subject with matched IDs, and any subjects missing the NIH Toolbox Dimensional Change Card Sort score are excluded with a log entry.

---

### User Story 2 - Dynamic Connectivity Metric Computation (Priority: P2)

The system MUST compute sliding-window Pearson correlation matrices for each subject using a fixed-duration window and a small step size., calculate the standard deviation (variability) and Shannon entropy for every edge across windows, and collapse these into a single subject-level variability metric.

**Why this priority**: This is the core transformation that operationalizes the research hypothesis. It converts raw fMRI time-series into the specific predictor variable (RSFC variability) required to test the relationship with cognitive flexibility.

**Independent Test**: The module can be tested by running it on a single subject's preprocessed time-series and verifying that the output CSV row contains a calculated variability metric (mean edge SD). Additionally, the Shannon entropy calculation MUST be verified by comparing the output against a manual calculation using the formula: H = -Σ p(x) * log(p(x)), where p(x) is the probability of correlation values falling into one of a set of equally spaced bins.

**Acceptance Scenarios**:

1. **Given** a subject's preprocessed 4D fMRI data, **When** the sliding-window analysis runs with a 60-second window and 1-second step, **Then** a sequence of correlation matrices is generated, and the standard deviation is calculated for every edge across this sequence.
2. **Given** the edge-wise standard deviations, **When** the aggregation step executes, **Then** a single scalar value representing the mean variability across all edges (or a weighted subset) is produced for that subject.
3. **Given** the correlation distribution for an edge, **When** the entropy calculation runs, **Then** the output is a non-negative float representing the Shannon entropy (base 2), which is included in the subject's feature vector.
4. **Given** the preprocessed time-series, **When** a null-model validation runs (phase-shuffled time series), **Then** the system confirms that the variability metric derived from real data is statistically significantly higher (p < 0.05) than the metric derived from the null model, ensuring the metric captures neural dynamics and not just noise.

---

### User Story 3 - Statistical Association and Significance Testing (Priority: P3)

The system MUST perform a regression analysis of cognitive flexibility scores on the RSFC variability metric (controlling for covariates) and validate the significance of the association using a permutation test with a sufficient number of iterations., outputting the p-value and confidence intervals.

**Why this priority**: This step answers the primary research question. It determines whether the observed relationship is statistically robust and distinguishes signal from noise, fulfilling the "Expected Results" criteria of the idea.

**Independent Test**: The analysis can be tested by running the regression and permutation test on a mock dataset generated with a known ground-truth correlation (r=0.5, n=100). The system MUST output a p-value that aligns with the theoretical expectation within an acceptable tolerance. (e.g., if theoretical p < 0.001, observed must be < 0.01).

**Acceptance Scenarios**:

1. **Given** the subject-level dataset with variability metrics and flexibility scores, **When** the regression model runs, **Then** the output includes the regression coefficient (β), standard error, and the Pearson correlation coefficient (r) between variability and flexibility.
2. **Given** the observed regression statistic, **When** the 10,000-permutation test executes, **Then** the system generates a null distribution by shuffling the behavioral scores and calculates the empirical p-value as the proportion of permuted statistics exceeding the observed statistic.
3. **Given** the analysis results, **When** the report is generated, **Then** it includes a plot of variability vs. flexibility with a regression line and 95% confidence interval, and a text summary stating whether the association is significant (p < 0.05) or not.
4. **Given** a scenario where post-hoc network-specific analyses are performed, **When** the results are reported, **Then** the p-values MUST be adjusted using False Discovery Rate (FDR) correction (q < 0.05) to control for multiple comparisons.

---

### Edge Cases

- **What happens when** a subject has excessive motion (Mean Framewise Displacement > 0.2mm) such that the sliding-window correlation becomes unreliable? **Then** the system MUST exclude that subject from the final analysis and log the exclusion reason.
- **How does the system handle** subjects who have fMRI data but are missing the NIH Toolbox Dimensional Change Card Sort score? **Then** the system MUST drop these subjects during the data merging phase and report the count of dropped subjects.
- **What happens when** the permutation test yields a p-value of exactly 0.0 (no permuted statistics exceed the observed)? **Then** the system MUST report the p-value as `< 0.0001` (1/10,000) rather than 0.0 to avoid mathematical errors in downstream interpretation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download the HCP 1200-subject resting-state fMRI and behavioral data from the specified source and verify file integrity before processing. (See US-1)
- **FR-002**: The system MUST apply the Schaefer atlas to parcellate the preprocessed fMRI time-series for every subject. (See US-1)
- **FR-003**: The system MUST compute sliding-window Pearson correlation matrices (window=60s, step=1s) and calculate the standard deviation and Shannon entropy for every edge. (See US-2)
- **FR-004**: The system MUST collapse edge-wise variability metrics into a single subject-level predictor variable for the regression analysis. (See US-2)
- **FR-005**: The system MUST perform a linear regression of flexibility scores on the variability metric while controlling for age, sex, mean framewise displacement, and total scan time. (See US-3)
- **FR-006**: The system MUST execute a large-scale permutation test. to generate a null distribution and calculate an empirical p-value for the regression coefficient. (See US-3)
- **FR-007**: The system MUST output a CSV file containing subject IDs, the variability metric, flexibility scores, covariates, and the regression results. (See US-3)
- **FR-008**: The system MUST validate the construct validity of the RSFC variability metric by comparing it against a null model of phase-shuffled time series, ensuring the observed variability is significantly higher than noise (p < 0.05). (See US-2)
- **FR-009**: The system MUST restrict statistical inference to a single global test of the primary hypothesis; if any post-hoc network-specific analyses are conducted, the system MUST apply False Discovery Rate (FDR) correction with a threshold of q ≤ 0.05. (See US-3)

### Key Entities

- **Subject**: An individual participant with associated fMRI data and behavioral scores. Attributes: ID, Age, Sex, Mean Framewise Displacement, Total Scan Time.
- **RSFC Variability Metric**: A scalar value derived from the standard deviation of sliding-window correlations, representing the dynamic fluctuation of functional connectivity.
- **Flexibility Score**: The behavioral outcome variable derived from the NIH Toolbox Dimensional Change Card Sort task.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of subjects successfully processed (passing motion and data quality checks) is measured against the total number of subjects in the HCP 1200 release subset used. (See US-1)
- **SC-003**: The empirical p-value derived from the 10,000 permutations is measured against the significance threshold of 0.05 (or FDR-adjusted q ≤ 0.05 for post-hoc tests) to determine hypothesis support. (See US-3)
- **SC-004**: The correlation coefficient (r) between RSFC variability and flexibility scores is measured against the null hypothesis of no association (r=0) to assess effect direction and magnitude. (See US-3)

## Assumptions

- The HCP 1200 release provides resting-state fMRI data that has already undergone minimal preprocessing (motion correction, ICA-FIX denoising) as required by the methodology sketch.
- The NIH Toolbox Dimensional Change Card Sort scores are available in the HCP behavioral data files for the majority of the subjects.
- The sliding-window correlation approach with a sufficiently long window is sufficient to reliably estimate correlation matrices for a substantial number of regions., avoiding the "noise floor" artifact associated with shorter windows.
- The Schaefer 200-region atlas is compatible with the HCP MNI space used in the preprocessed data.
- The analysis will be observational; therefore, findings will be framed as associational rather than causal, consistent with the lack of random assignment in the HCP dataset.
- The GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) is sufficient to process the data and run the permutation test within 6 hours, provided the data is processed in batches or optimized for CPU usage.
- The memory usage of the pipeline will not exceed a predefined threshold (peak RSS of the Python process)..
- The "variability" metric will be defined as the mean standard deviation of edge-wise correlations across all edges, as specified in the expected results.
- The permutation test will use a sufficient number of iterations as the standard for robust p-value estimation., balancing accuracy with compute time.
- Covariates (age, sex, motion, scan time) will be included as control variables in the regression model to isolate the effect of RSFC variability.
- The analysis will not require GPU acceleration; all computations will be performed using CPU-optimized libraries (numpy, scipy, statsmodels).
- The construct validity of the variability metric is supported by the null-model comparison (FR-008), ensuring the metric reflects neural dynamics rather than thermal noise or estimation error.