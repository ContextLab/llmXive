# Data Model: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## 1. Overview

This document defines the data structures used throughout the pipeline. All data flows from `raw` (downloaded) to `processed` (cleaned/extracted) to `models` (trained).

## 2. Entity Definitions

### 2.1 EEG Epoch
Represents a short-duration window of filtered EEG data.
*   **subject_id**: Unique identifier for the participant.
*   **condition**: `rest` or `task`.
*   **channel**: Channel name (e.g., `C3`, `C4`, `Fz`).
*   **time**: Timestamp relative to epoch start (seconds).
*   **voltage**: Amplitude in microvolts (µV).

### 2.2 Feature Vector
Aggregated metrics per subject.
*   **subject_id**: Unique identifier.
*   **mode**: `positive_control` (synthetic with injected signal) or `structural_validation` (random noise).
*   **power_delta**: Mean power in the low-frequency band.
*   **power_theta**: Mean power in a low-frequency band.
*   **power_alpha**: Mean power in –13 Hz band.
*   **power_beta**: Mean power in the beta frequency band.
*   **power_gamma**: Mean power in –45 Hz band.
*   **plv_c3_c4**: Phase Locking Value between C3 and C4 (Motor ROI).
*   **plv_c3_cz**: Phase Locking Value between C3 and Cz (Motor ROI).
*   **plv_c4_cz**: Phase Locking Value between C4 and Cz (Motor ROI).
*   **plv_mean_global**: Mean Phase Locking Value across all pairs.
*   **wpli_c3_c4**: Weighted Phase Lag Index between C3 and C4 (Motor ROI).
*   **wpli_mean_global**: Mean Weighted Phase Lag Index across all pairs.
*   **tdcs_response**: Percentage change in motor score (Synthetic: injected signal + noise).
*   **injected_signal_strength**: Known correlation coefficient used to generate target (e.g., a small positive magnitude).

### 2.3 Model Output
*   **model_type**: `ridge`.
*   **alpha**: Regularization parameter used.
*   **r2_adjusted**: Adjusted R-squared value.
*   **p_permutation**: P-value from permutation test.
*   **fdr_corrected_p**: P-value after FDR correction.
*   **status**: `valid` (detected injected signal) or `pipeline_broken` (failed to detect signal).
*   **stability_variance**: Variance in significance status across sensitivity sweep.

## 3. Data Flow

1.  **Ingestion**: Raw CSV/Parquet files downloaded to `data/raw`.
2.  **Preprocessing**: Filtered, re-referenced, epoched. Output: `data/processed/epochs.fif` (MNE format) or `data/processed/epochs.csv`.
3.  **Feature Extraction**: Spectral/Connectivity features computed (ROI specific). Output: `data/processed/features.csv`.
4.  **Modeling**: Ridge regression fit. Output: `models/ridge_model.pkl` and `data/processed/model_metrics.json`.
5.  **Validation**: Permutation/FDR results. Output: `data/processed/validation_report.csv`.

## 4. Constraints

*   **Data Integrity**: Raw files never modified. Checksums recorded (SHA-256).
*   **Memory**: The feature matrix must fit in available system RAM. If `n_subjects * n_features` > threshold, subsample epochs.
*   **Privacy**: No PII in `data/processed` or `models/`. Subject IDs are anonymized.
*   **Synthetic Target**: In Positive Control Mode, `tdcs_response` must be generated with a known `injected_signal_strength` and verified to be decoupled from noise.