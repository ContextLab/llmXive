# Methodology Notes: Neural Entropy and Cognitive Flexibility in Aging

**Project**: PROJ-454-investigating-the-relationship-between-n
**Version**: 1.0
**Date**: 2024

## 1. Overview

This document details the processing steps, statistical assumptions, and methodological decisions made in the investigation of the relationship between neural entropy (Sample Entropy and Approximate Entropy) and cognitive flexibility (measured via WCST perseverative errors) in aging populations.

## 2. Data Sources and Acquisition

### 2.1 Primary Data
- **Source**: OpenNeuro (ds003104 and related datasets).
- **Acquisition**: Automated download via `code/01_download_data.py`.
- **Verification**: Variable fit check performed to ensure presence of `wcst_perseverative_errors` and `age >= 50` criteria.
- **Format**: Raw data stored in `data/raw/` as Parquet files with SHA256 checksums.

### 2.2 Behavioral Data
- **Extraction**: Behavioral scores (WCST errors, age, education, etc.) extracted to `data/processed/behavioral_scores.csv`.
- **Validation**: Explicit check for `wcst_perseverative_errors` column; pipeline halts with `DATASET_VARIABLE_MISMATCH` if missing.

## 3. EEG Preprocessing Pipeline

Implemented in `code/02_preprocess_eeg.py`.

### 3.1 Filtering
- **Bandpass**: 1 Hz to 45 Hz (Butterworth filter).
- **Notch**: 50 Hz or 60 Hz (depending on region) to remove line noise.

### 3.2 Artifact Correction
- **Bad Channel Interpolation**: Identified channels interpolated using spherical splines.
- **ICA**: Independent Component Analysis performed for ocular and cardiac artifact removal.

### 3.3 Epoching
- **Segmentation**: Non-overlapping 2-second epochs extracted.
- **Baseline Correction**: Applied relative to pre-stimulus interval (if available) or global mean.

### 3.4 Quality Control (QC)
Participants are excluded if:
- Valid EEG duration < 60 seconds.
- Corrupted segments > 20% of total recording.
- **SNR < 5 dB** (calculated as `median(signal_power_1-45Hz) / median(noise_power_residual)`).
- Exclusion reasons logged in `data/processed/exclusion_log.csv`.

## 4. Entropy Computation

Implemented in `code/compute_entropy.py` using `utils/entropy_utils.py`.

### 4.1 Algorithms
- **Sample Entropy (SampEn)**: Computed for all frequency bands.
- **Approximate Entropy (ApEn)**: Computed for all frequency bands.
- **Parameters**: Standard parameters (m=2, r=0.2*std) used unless specified otherwise in sensitivity analysis.

### 4.2 Frequency Bands
- **Delta**: 1–4 Hz
- **Theta**: 4–8 Hz
- **Alpha**: 8–13 Hz
- **Beta**: 13–30 Hz
- **Gamma**: 30–45 Hz

### 4.3 Output
- Results stored in `data/processed/entropy_metrics.csv`.
- Both SampEn and ApEn included for all bands.

## 5. Statistical Analysis Strategy

Implemented in `code/04_regression_analysis.py`.

### 5.1 Primary Model: Multiple Linear Regression (OLS)
- **Dependent Variable**: WCST Perseverative Errors.
- **Independent Variables**: Entropy metrics (SampEn/ApEn) across bands.
- **Covariates**: Age, Education, Task Accuracy, Neurological Condition, Medication status.
- **Rationale**: Replaces Partial Pearson correlation per project plan deviation to better control for confounding variables simultaneously.

### 5.2 Multicollinearity Check
- **Method**: Variance Inflation Factor (VIF).
- **Threshold**: VIF > 5.
- **Action**: If VIF > 5 for any entropy metric, Approximate Entropy (ApEn) is dropped, and the model is re-run with Sample Entropy (SampEn) only to ensure stability.

### 5.3 Multiple Comparison Correction
- **Primary Method**: Benjamini-Hochberg (FDR) correction.
- **Scope**: Applied to all p-values resulting from the OLS model (5 bands × remaining entropy metrics).
- **Rationale**: Chosen over Bonferroni to maintain statistical power while controlling the False Discovery Rate (Plan deviation from original Spec FR-004).

### 5.4 Effect Size Calculation
- **Metric**: Partial R.
- **Classification**: |Partial R| ≥ 0.3 classified as "clinically meaningful".
- **Output**: `data/processed/effect_sizes.json`.

### 5.5 Historical Comparison (Constitution Amendment Tracking)
- **Method**: Bonferroni correction calculated for historical tracking only.
- **Output**: `data/processed/correlation_results_bonferroni_historical.csv`.
- **Note**: Explicitly marked as non-primary in all reports.

## 6. Sensitivity Analysis

Implemented in `code/04_regression_analysis.py`.

### 6.1 Exclusion Sensitivity
- **Scenario**: Re-running regression excluding participants with known neurological conditions or specific medications.
- **Output**: `data/processed/sensitivity_exclusion_results.csv`.

### 6.2 Threshold Sensitivity
- **Artifact Rejection**: Swept from 15% to 25% amplitude deviation.
- **SNR Threshold**: Swept from baseline to 7 dB.
- **Output**: `data/processed/sensitivity_threshold_results.csv`.

### 6.3 Reporting
- **Summary**: `data/processed/sensitivity_report.json` compares correlation rates and significance across all scenarios.

## 7. Assumptions and Limitations

1. **Associational Nature**: All findings are associational. No causal claims are made regarding neural entropy and cognitive flexibility.
2. **Sample Size**: Power analysis requirements are deferred; the study acknowledges potential limitations in detecting small effect sizes (as noted in `logs/power_analysis.log`).
3. **Data Quality**: Relies on the assumption that OpenNeuro datasets are pre-processed to a standard compatible with the defined pipeline.
4. **Entropy Parameters**: The choice of m=2 and r=0.2*std is standard but may not be optimal for all specific EEG frequency bands; sensitivity to these parameters was not exhaustively tested in the primary run.

## 8. Reproducibility

- **Code**: All scripts are version-controlled and located in `code/`.
- **Dependencies**: Pinned in `code/requirements.txt`.
- **Data**: Raw data sources are referenced via checksums in `data/raw/`.
- **Environment**: CPU-only execution enforced; no GPU dependencies.

## 9. Disclaimer

This research is for scientific investigation purposes. The methodology, specifically the use of OLS with FDR correction, represents a deviation from the original specification to align with updated project planning. Users of this data should consult the `reports/final_report.md` for the complete associational disclaimer and covariate summary.