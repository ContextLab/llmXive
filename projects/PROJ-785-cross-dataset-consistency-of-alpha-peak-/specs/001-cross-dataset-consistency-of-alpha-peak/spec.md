# Feature Specification: Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG

**Feature Branch**: `001-cross-dataset-apf-consistency`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Dual-Pipeline Preprocessing (Priority: P1)

**User Journey**: As a neuroscientist, I want to automatically download 3-5 specific resting-state EEG datasets from OpenNeuro (e.g., ds003865, ds003392, ds003775) and apply TWO distinct standardized preprocessing pipelines to all data so that I can compare the consistency of the Alpha Peak Frequency (APF) biomarker across different methodological choices.

**Pipeline A (Standard)**: Bandpass filtering, notch filtering at the mains frequency., common average reference, ICA-based ocular artifact rejection.
**Pipeline B (Alternative)**: Bandpass with a low-frequency cutoff, notch at power-line frequency, mastoid reference, NO ICA (raw data retained).

**Why this priority**: This is the foundational step. Without acquiring data and applying distinct pipelines, no variance decomposition can occur. This addresses the "pipeline" variable in the research question by ensuring it has non-zero variance.

**Independent Test**: The system can be tested by executing the download and preprocessing scripts on a single dataset and verifying that output files exist for BOTH Pipeline A and Pipeline B in the expected BIDS-compliant derivative format with no NaN values in the signal channels.

**Acceptance Scenarios**:

1. **Given** a list of valid OpenNeuro dataset IDs, **When** `scripts/download_openneuro.py` runs, **Then** the raw EEG data (BIDS format) is successfully retrieved and stored locally within a predefined timeout period..
2. **Given** raw EEG data with artifacts, **When** Pipeline A runs, **Then** the output contains cleaned signals where the 50/60Hz notch filter has attenuated line noise by ≥ 20dB and ICA has removed ocular artifacts (verified by automated rejection of components where correlation with EOG channel > 0.8 or frontal variance > 15%).
3. **Given** a dataset with missing metadata, **When** the validation step runs, **Then** the system halts and logs a specific error identifying the missing field rather than proceeding with incomplete data.
4. **Given** the same raw dataset, **When** Pipeline B runs, **Then** the output contains signals re-referenced to mastoids with a low-pass and high-pass bandpass filter and no ICA components removed.

---

### User Story 2 - Alpha Peak Frequency (APF) Estimation via Dual Methods (Priority: P2)

**User Journey**: As a researcher, I want to calculate the Alpha Peak Frequency (APF) for every subject in every dataset using two distinct methods (time-domain autocorrelation and frequency-domain PSD peak detection within 8-13 Hz) so that I can compare the consistency of the biomarker across different estimation techniques.

**Why this priority**: This generates the dependent variable (APF). The dual-method approach is critical to determining if the variability observed is due to the estimation algorithm itself or the dataset source.

**Independent Test**: The system can be tested by running the APF estimation on a synthetic EEG signal with a known, injected alpha peak (e.g., 10.0 Hz) and verifying that both methods return a value within ±0.5 Hz of the ground truth.

**Acceptance Scenarios**:

1. **Given** a cleaned EEG epoch from a subject, **When** the PSD method runs, **Then** it identifies the maximum spectral power within the low-frequency range and reports the corresponding frequency as the APF.
2. **Given** a cleaned EEG epoch, **When** the autocorrelation method runs, **Then** it detects the first significant peak in the autocorrelation function corresponding to the alpha band and converts it to frequency.
3. **Given** a subject with no clear alpha peak (flat spectrum), **When** either method runs, **Then** the system flags the result as "Indeterminate" rather than returning a random noise frequency.

---

### User Story 3 - Variance Decomposition and Reporting (Priority: P3)

**User Journey**: As a principal investigator, I want to fit a mixed-effects model to decompose the variance in APF estimates into components attributable to "Dataset Source", "Preprocessing Pipeline" (A vs B), and "Estimation Method" so that I can determine the reproducibility of the biomarker.

**Why this priority**: This answers the core research question. It synthesizes the data and methods to provide the final scientific insight regarding cross-study consistency.

**Independent Test**: The system can be tested by running the analysis on a simulated dataset where the "Dataset Source" variance is set to 0.40, "Pipeline" variance is set to 0.10, and "Residual" variance is set to 0.50, verifying that the model recovers these proportions within a reasonable margin of error.

**Acceptance Scenarios**:

1. **Given** the aggregated APF values per subject per dataset per pipeline, **When** the mixed-effects model (APF ~ dataset_source + pipeline_type + estimation_method + (1|subject)) runs, **Then** it outputs the R² (variance explained) for the fixed effects (dataset, pipeline, method) and the random effect (subject).
2. **Given** the variance components, **When** the bootstrapping procedure runs (A substantial number of resamples), **Then** it generates % confidence intervals for each variance component.
3. **Given** the final results, **When** the report is generated, **Then** it includes a forest plot of APF by dataset and a bar chart showing the percentage of total variance attributed to each factor.

### Edge Cases

- **What happens when** a dataset from OpenNeuro has incomplete BIDS metadata (e.g., missing sampling frequency)? The system must skip the dataset and log a "Data Integrity" warning, rather than crashing or imputing incorrect values.
- **How does the system handle** subjects where the alpha peak falls outside the 8-13 Hz range (e.g., 7.5 Hz or 14 Hz)? The system must flag these as "Out-of-Band" and exclude them from the primary mean calculation, reporting them separately.
- **What happens when** the ICA component rejection fails to identify any ocular artifacts in a specific subject (Pipeline A)? The system must proceed with the raw data for that subject but flag the "Artifact Rejection Status" as "None Detected" in the metadata.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download at least 3 distinct resting-state EEG datasets from OpenNeuro that contain at least 20 subjects each and verify BIDS compliance before processing. (See US-1)
- **FR-002**: System MUST apply TWO distinct preprocessing pipelines to ALL downloaded datasets: 
  (A) Bandpass low-frequency to a low cutoff frequency., notch / Hz, common average reference, ICA artifact rejection.
  (B) Bandpass filtering will be applied to isolate the relevant frequency band, with lower and upper cutoffs determined by the characteristics of the target signal and noise profile., notch /60 Hz, mastoid reference, no ICA. (See US-1)
- **FR-003**: System MUST calculate Alpha Peak Frequency (APF) for every subject using two independent methods: (1) time-domain autocorrelation peak detection and (2) frequency-domain PSD peak detection within 8-13 Hz. (See US-2)
- **FR-004**: System MUST fit a linear mixed-effects model (APF ~ dataset_source + pipeline_type + estimation_method + (1|subject)) to perform variance decomposition. (See US-3)
- **FR-005**: System MUST perform a non-parametric bootstrapping procedure with a sufficient number of resamples to generate confidence intervals for all variance components. (See US-3)
- **FR-006**: System MUST perform a power analysis to estimate the minimum sample size required to detect a pipeline a small effect size with 80% power (α=0.05) and report the achieved power in the final results. (See US-3)

### Key Entities

- **EEG Dataset**: A collection of raw and preprocessed signal files associated with a specific OpenNeuro ID, containing metadata on sampling rate and channel layout.
- **APF Estimate**: A single float value representing the dominant alpha frequency for a specific subject, channel, estimation method, and preprocessing pipeline.
- **Variance Component**: A statistical metric (R² or sigma²) quantifying the proportion of total APF variability explained by a specific factor (Dataset, Pipeline, Method, Subject).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of APF variance attributable to "Dataset Source" is measured against the total variance (R²) to determine if biological/source factors dominate. Success is defined as R² for dataset source ≥ 0.30. (See US-3)
- **SC-002**: The consistency between the time-domain and frequency-domain APF estimates is measured against a threshold of ±0.5 Hz to validate the reliability of the dual-method approach. (See US-2)
- **SC-003**: The stability of the variance decomposition results is measured against the width of the 95% confidence intervals generated by the -sample bootstrapping procedure AND the achieved statistical power (must be ≥ 0.80 for the pipeline effect). (See US-3)
- **SC-004**: The computational feasibility is measured against the constraint of completing the full analysis (download, dual-pipeline preprocess, model, bootstrap) within 24 hours on a standard CPU-only CI runner with ≤16 GB RAM. If RAM is exceeded, the system must fall back to sequential dataset processing. (See US-3)
- **SC-005**: The methodological validity is measured by the inclusion of a sensitivity analysis for the alpha band definition (8-13 Hz) by sweeping the bounds by ±0.5 Hz and reporting the change in APF rates. Success is defined as the change in mean APF being ≤ 0.2 Hz across the swept bounds. (See US-2)

## Assumptions

- **Assumption about data availability**: The selected OpenNeuro datasets will remain publicly accessible and will not require authentication credentials beyond standard public access during the CI execution window.
- **Assumption about computational limits**: The total size of the raw EEG data for 3-5 datasets (N<50 subjects each) will fit within the ~16 GB RAM and ~ GB disk constraints of the GitHub Actions free-tier runner; if a dataset exceeds this, the system will assume the need to process datasets sequentially.
- **Assumption about alpha band definition**: The standard 8-13 Hz range is a valid community-standard definition for the alpha band in this context; however, the sensitivity analysis (SC-005) will test the robustness of this specific boundary.
- **Assumption about inference framing**: Since the datasets are observational and not randomized controlled trials, the variance decomposition results will be framed strictly as "associational" contributions to variance, not causal effects of the dataset source on the biological signal.
- **Assumption about method validity**: The ICA algorithm (e.g., FastICA) and PSD estimation methods (e.g., Welch's method) are assumed to be computationally tractable on CPU without GPU acceleration for the specified dataset sizes.
- **Assumption about variable fit**: The OpenNeuro datasets contain the necessary raw voltage time-series data required to compute APF; no derived features (like pre-calculated power spectra) are required from the source.
- **Assumption about power**: The minimum of 20 subjects per dataset (3-5 datasets) provides sufficient degrees of freedom to estimate the fixed effects, provided the power analysis (FR-006) confirms the effect size assumptions.