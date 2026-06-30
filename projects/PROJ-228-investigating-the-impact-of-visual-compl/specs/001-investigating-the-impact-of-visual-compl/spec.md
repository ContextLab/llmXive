# Feature Specification: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

**Feature Branch**: `001-visual-complexity-pfc`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How do quantitative measures of visual complexity (e.g., entropy, fractal dimension) in naturalistic stimuli correlate with BOLD signal amplitude in the prefrontal cortex (PFC) during passive viewing tasks?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion, HRF Convolution, and Stimulus Complexity Calculation (Priority: P1)

The system MUST download preprocessed fMRI data and stimulus logs from OpenNeuro (e.g., ds000246), compute quantitative visual complexity metrics (Shannon entropy and fractal dimension) for every stimulus frame, and convolve these metrics with a canonical Hemodynamic Response Function (HRF) to align them with the BOLD signal lag.

**Why this priority**: Without accurate computation of the predictor variables (complexity metrics) aligned with the stimulus presentation logs via HRF convolution, no correlation analysis can be performed. This is the foundational data preparation step that ensures temporal validity.

**Independent Test**: The system can be tested by running the ingestion script on a single subject's data, verifying that a CSV file is generated containing time-locked complexity scores (convolved with HRF) for every stimulus frame, and that the peak memory usage recorded in logs is ≤ 6GB.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID and local storage space > 14GB, **When** the ingestion script executes, **Then** the system downloads the preprocessed BOLD data and stimulus logs, computes entropy and fractal dimension for all images, convolves them with a canonical HRF (4-6s lag), and outputs a time-synced CSV file without triggering a memory overflow error.
2. **Given** a dataset with missing stimulus frames, **When** the script processes the data, **Then** the system flags the missing frames in the output log and excludes them from the complexity calculation rather than crashing.

---

### User Story 2 - ROI Extraction and Fixed Preprocessing (Priority: P2)

The system MUST extract the mean BOLD time-series from the Dorsolateral Prefrontal Cortex (DLPFC) using a standard atlas mask (e.g., AAL) and apply fixed preprocessing: 4mm FWHM spatial smoothing and z-score normalization within the ROI.

**Why this priority**: This step transforms the raw 4D fMRI data into a 1D time-series of the outcome variable (PFC activity) required for the regression analysis. Fixed smoothing (4mm) is critical to increase signal-to-noise ratio (SNR) for ROI-based analyses, ensuring the study is sufficiently powered to detect correlations.

**Independent Test**: The system can be tested by running the extraction module on a single subject's preprocessed data, verifying that the output is a 1D array of BOLD signal values aligned with the TR (Repetition Time), that smoothing and normalization have been applied, and that the file size is negligible compared to the raw 4D data.

**Acceptance Scenarios**:

1. **Given** the preprocessed BOLD data and the AAL atlas mask, **When** the extraction script runs, **Then** the system applies 4mm FWHM smoothing and z-score normalization, then outputs a CSV containing the mean PFC BOLD signal per timepoint, aligned with the stimulus timeline.
2. **Given** a dataset where the atlas mask partially overlaps the brain volume, **When** the extraction occurs, **Then** the system calculates the mean only over valid voxels within the mask and reports the number of excluded voxels in the log.

---

### User Story 3 - Statistical Modeling and Validation (Priority: P3)

The system MUST perform linear regression analysis between the HRF-convolved complexity metrics and PFC BOLD signal, apply FDR correction for the two metrics (entropy and fractal dimension), and run a sufficient number of circular block permutation tests to validate the null distribution while preserving temporal autocorrelation.

**Why this priority**: This is the core research output. It generates the correlation coefficients, p-values, and confidence intervals required to answer the research question while controlling for false positives and respecting the temporal structure of fMRI data.

**Independent Test**: The system can be tested by running the analysis script on the processed data from User Stories 1 and 2, verifying that a results JSON is produced containing correlation coefficients, p-values, FDR-corrected p-values, and the results of the circular block permutation test, all completed within the CI time limit.

**Acceptance Scenarios**:

1. **Given** the HRF-convolved complexity metrics and PFC time-series, **When** the regression model executes, **Then** the system outputs a correlation coefficient (r) and p-value for each complexity metric, and reports that the analysis completed within 60 minutes.
2. **Given** the regression results, **When** the circular block permutation test runs (1000 iterations), **Then** the system generates a null distribution histogram and confirms whether the observed correlation falls outside the 95% confidence interval of the null.

---

### Edge Cases

- What happens if the OpenNeuro dataset `ds000246` is unavailable or the specific visual task subset is missing? (System should fail gracefully with a clear error message and not attempt to proceed).
- How does the system handle subjects with excessive motion artifacts that result in invalid BOLD signal in the PFC? (System should flag these subjects in the log and exclude them from the group-level analysis).
- What happens if the computed fractal dimension values are NaN or infinite due to image artifacts? (System should replace these with 0 or exclude the specific frame and log the incident).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download preprocessed fMRI data and stimulus logs from OpenNeuro (e.g., ds000246) using `wget` and verify file integrity before processing. (See US-1)
- **FR-002**: System MUST compute Shannon entropy and fractal dimension for every stimulus image frame using `scikit-image` and `numpy`, convolve these metrics with a canonical HRF (4-6s lag), and process images in batches to ensure peak RAM usage does not exceed 6GB. (See US-1)
- **FR-003**: System MUST extract the mean BOLD time-series from the Dorsolateral Prefrontal Cortex (DLPFC) using the AAL atlas mask, applying 4mm FWHM spatial smoothing and z-score normalization to ensure sufficient signal-to-noise ratio. (See US-2)
- **FR-004**: System MUST perform linear regression with complexity metrics as predictors and PFC BOLD signal as the outcome, applying FDR correction for multiple comparisons across the two metrics (entropy and fractal dimension) within the single DLPFC ROI. (See US-3)
- **FR-005**: System MUST execute circular block permutation tests to establish null distributions that preserve temporal autocorrelation and validate that results are not driven by chance. (See US-3)

### Key Entities

- **Stimulus Complexity Record**: Represents a single stimulus frame with attributes: `frame_id`, `timestamp`, `entropy_score`, `fractal_dimension`, `hrf_convolved_score`.
- **PFC Time-Series**: Represents the aggregated BOLD signal for the DLPFC region with attributes: `timepoint`, `bold_signal_mean`, `subject_id`.
- **Regression Result**: Represents the statistical output with attributes: `correlation_coefficient`, `p_value`, `fdr_corrected_p`, `permutation_p`, `is_significant`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system outputs a boolean flag `is_significant` indicating whether the correlation is significant (p < 0.05) based on the circular block permutation test results. (See US-3)
- **SC-002**: The false discovery rate (FDR) is measured against the family-wise error rate threshold to ensure robustness of multiple comparisons across the two complexity metrics. (See US-3)
- **SC-003**: The stability of the correlation estimate is measured against a confidence interval derived from circular block permutation iterations. (See US-3)
- **SC-004**: The computational feasibility is measured against the GitHub Actions free-tier constraint of ≤6GB RAM and ≤6 hours total execution time. (See US-1, US-2)

## Assumptions

- The OpenNeuro dataset `ds000246` (or equivalent visual task subset) contains preprocessed fMRI data and stimulus logs sufficient for the analysis without requiring new data collection.
- The AAL atlas mask provides adequate coverage of the Dorsolateral Prefrontal Cortex (DLPFC) for extracting a representative mean time-series.
- The visual complexity metrics (entropy and fractal dimension) computed via `scikit-image` are valid proxies for the "visual complexity" construct relevant to PFC engagement.
- The free-tier GitHub Actions runner (multiple CPU cores, sufficient RAM) is sufficient to process the data in subject-wise chunks without exceeding memory limits, assuming standard 4mm smoothing is applied.
- The analysis is observational; findings will be framed as associational correlations, not causal effects, as there is no random assignment of stimulus complexity.
- The dataset contains the necessary variables (stimulus images and BOLD signal) and does not require additional covariates (e.g., post-task anxiety) that are absent from the source.
- The canonical HRF model (e.g., double-gamma) is sufficient to model the hemodynamic lag for the stimuli used in the dataset.