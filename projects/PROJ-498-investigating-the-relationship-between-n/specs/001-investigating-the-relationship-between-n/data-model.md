# Data Model: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

## 1. Overview

This document defines the data structures used throughout the pipeline. All data is stored in `data/` (raw, interim, processed) and validated against schemas in `contracts/`.

## 2. Entity Definitions

### 2.1 Raw Data (EEG)
*   **Source**: OpenNeuro ds004173 (BIDS format).
*   **Structure**: Directory tree with `sub-<id>/eeg/sub-<id>_task-<task>_eeg.edf` (or .bdf/.vhdr) and `sub-<id>/eeg/sub-<id>_task-<task>_events.tsv`.
*   **Key Fields**:
    *   `subject_id`: String (e.g., "sub-01").
    *   `task`: String (e.g., "switch").
    *   `onset`: Float (seconds).
    *   `trial_type`: String (e.g., "switch", "stay").
    *   `response_time`: Float (ms).
    *   `accuracy`: Integer (0/1).

### 2.2 Preprocessed Data (EEG_Epoch)
*   **Source**: `code/preprocess_eeg.py`.
*   **Format**: HDF5 or NumPy `.npy` (for speed) / CSV (for inspection).
*   **Structure**:
    *   `subject_id`: String.
    *   `trial_id`: Integer.
    *   `condition`: String ("switch" or "stay").
    *   `time_series`: Array of shape `(n_channels, n_times)`.
    *   `is_valid`: Boolean (True if artifact < 20%).

### 2.3 Behavioral Data (Behavioral_Trial)
*   **Source**: Extracted from events.tsv.
*   **Format**: CSV.
*   **Schema**:
    *   `subject_id`: String.
    *   `trial_id`: Integer.
    *   `condition`: String.
    *   `reaction_time`: Float (ms).
    *   `accuracy`: Integer (0/1).
    *   `log_rt`: Float (log-transformed RT).

### 2.4 Synchrony Features (Synchrony_Feature)
*   **Source**: `code/compute_synchrony.py`.
*   **Format**: CSV.
*   **Schema**:
    *   `subject_id`: String.
    *   `trial_id`: Integer.
    *   `electrode_pair`: String (e.g., "F3-P3").
    *   `frequency_band`: String ("theta", "gamma").
    *   `metric_type`: String ("IPD" or "wPLI").
    *   `phase_difference`: Float (radians, -π to π). (Only for IPD)
    *   `wpli_value`: Float (0 to 1). (Only for wPLI)
    *   `sin_phase`: Float. (Transformed for IPD)
    *   `cos_phase`: Float. (Transformed for IPD)
    *   `window`: String ("pre-stimulus").

### 2.5 Statistical Results (Statistical_Result)
*   **Source**: `code/analyze_lmm.py`.
*   **Format**: CSV / JSON.
*   **Schema**:
    *   `model_id`: String.
    *   `metric_type`: String ("IPD" or "wPLI").
    *   `electrode_pair`: String.
    *   `frequency_band`: String.
    *   `fixed_effect_sin`: Float (for IPD interaction).
    *   `fixed_effect_cos`: Float (for IPD interaction).
    *   `fixed_effect_wpli`: Float (for wPLI interaction).
    *   `std_error_sin`: Float.
    *   `std_error_cos`: Float.
    *   `std_error_wpli`: Float.
    *   `p_value_uncorrected`: Float.
    *   `p_value_corrected`: Float.
    *   `correction_method`: String ("bonferroni", "fdr").
    *   `permutation_p_value`: Float.
    *   `convergence_status`: String ("converged", "failed").
    *   `joint_test_p_value`: Float (LRT p-value for IPD interaction).
    *   `direction_vector`: String (JSON string representing the (sin, cos) interaction vector for IPD).

## 3. Data Flow

1.  **Download**: Raw BIDS data → `data/raw/`.
2.  **Preprocess**: Raw → `data/interim/preprocessed_epochs.npy` + `data/interim/behavioral.csv`.
3.  **Synchrony**: Preprocessed + Behavioral → `data/interim/synchrony_features.csv`.
4.  **Analysis**: Synchrony + Behavioral → `data/processed/lmm_results.csv`.
5.  **Validation**: `data/processed/lmm_results.csv` validated against `contracts/lmm_results.schema.yaml`.

## 4. Constraints

*   **Memory**: Intermediate arrays (e.g., `time_series`) must be discarded after feature extraction.
*   **Precision**: Floating point values stored as `float32` to save disk/RAM unless double precision is required for statistical stability (LMM usually requires `float64` for the model matrix, but features can be `float32`).
*   **Missing Data**: Subjects with missing trials are logged and excluded; they are not imputed.