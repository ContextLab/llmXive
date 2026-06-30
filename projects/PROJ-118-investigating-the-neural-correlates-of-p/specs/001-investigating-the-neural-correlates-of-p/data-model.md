# Data Model: Investigating the Neural Response to Deviance in Auditory Perception

## Overview

This document defines the data structures used in the pipeline. All data is derived from the OpenNeuro dataset. The model ensures traceability from raw EEG to statistical results.

## Entities

### 1. Raw EEG Record
*   **Source**: OpenNeuro ds003645
*   **Format**: BIDS (`.fif` or `.edf`)
*   **Description**: Unprocessed EEG recordings containing standard and deviant auditory stimuli.
*   **Constraints**: Stored in `data/raw/`. Immutable.

### 2. Preprocessed Epochs
*   **Source**: Raw EEG Record (filtered, re-referenced, ICA-cleaned)
*   **Format**: MNE Epochs (`.fif`)
*   **Description**: Time-locked segments (-200ms to 600ms) labeled "standard" or "deviant".
*   **Attributes**:
    *   `subject_id`: Participant identifier.
    *   `condition`: "standard" or "deviant".
    *   `channels`: Subsampled to a reduced set of channels (Fz, FCz, Cz, Pz, etc.).
    *   `sampling_rate`: Original sampling rate (e.g., a high frequency appropriate for the signal bandwidth).

### 3. Difference Wave Epochs
*   **Source**: Preprocessed Epochs
*   **Format**: MNE Epochs (`.fif`) or NumPy Array
*   **Description**: The difference between Deviant and Standard ERPs (Deviant - Standard) for each participant.
*   **Attributes**:
    *   `subject_id`: Participant identifier.
    *   `channels`: Same as Preprocessed Epochs.
    *   `time_window`: -200ms to 600ms.

### 4. MMN Metrics
*   **Source**: Difference Wave Epochs
*   **Format**: CSV / JSON
*   **Description**: Extracted peak amplitude and latency for each participant and electrode from the **Difference Wave**.
*   **Attributes**:
    *   `subject_id`: Participant identifier.
    *   `electrode`: Fz or FCz.
    *   `condition`: "difference" (derived from Deviant - Standard).
    *   `amplitude`: Peak voltage of difference wave (µV). **Nullable** if no peak detected.
    *   `latency`: Time of peak (ms). **Nullable** if no peak detected.
    *   `peak_detected`: Boolean (True if peak found in primary/fallback window).
    *   `snr`: Signal-to-Noise Ratio of the peak.
    *   `is_excluded`: Boolean (True only if >50% trials rejected due to artifacts).

### 5. Statistical Results
*   **Source**: MMN Metrics
*   **Format**: JSON
*   **Description**: Results of t-tests, cluster permutation, and mixed-effects models.
*   **Attributes**:
    *   `comparison`: "deviant_vs_standard" (difference score).
    *   `metric`: "amplitude" or "latency".
    *   `electrode`: Fz or FCz.
    *   `t_stat`: T-statistic value.
    *   `p_value`: Raw p-value.
    *   `p_value_fdr`: FDR-corrected p-value.
    *   `cohens_d`: Effect size.
    *   `ci_95`: 95% Confidence Interval (lower, upper).
    *   `cluster_p`: P-value from cluster-based permutation test.
    *   `mixed_effects_p`: P-value from mixed-effects model.
    *   `prevalence`: Proportion of participants with `peak_detected=true`.

## Data Flow

1.  `Raw EEG` → (Filter, Re-reference, ICA, Epoch) → `Preprocessed Epochs`
2.  `Preprocessed Epochs` → (Deviant - Standard) → `Difference Wave Epochs`
3.  `Difference Wave Epochs` → (Peak Detection) → `MMN Metrics`
4.  `MMN Metrics` → (T-test, FDR, Cluster, Mixed-effects) → `Statistical Results`
5.  `Statistical Results` + `Difference Wave Epochs` → (Plotting) → `Visualizations`

## Integrity Constraints

*   **Raw Data**: Never modified.
*   **Derived Data**: New files created for each transformation step.
*   **Checksums**: All files in `data/` must have a corresponding checksum in `state.yaml`.
*   **Outliers**: Participants with >50% artifact rejection are marked `is_excluded=true` and removed from analysis. Participants with no peak are marked `peak_detected=false` but **included** in prevalence counts.
*   **Null Handling**: If `peak_detected=false`, `amplitude` and `latency` are stored as `null` (not 0.0) to avoid biasing the mean.
