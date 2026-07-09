# Data Model: Cross-Modal Comparison of Neural Prediction Error Signals

## Overview

This document defines the data structures, schemas, and file formats used throughout the pipeline. All data artifacts are versioned via content hashing.

## Entity Definitions

### 1. NeuralSignal
Represents preprocessed EEG/MEG data.
-   **Attributes**:
    -   `subject_id`: str
    -   `modality`: enum['auditory', 'visual']
    -   `sampling_rate`: float (Hz)
    -   `n_trials`: int (oddball), int (standard)
    -   `electrodes`: list[str]
    -   `artifact_rejected`: bool
    -   `checksum`: str (SHA-256)

### 2. PredictionErrorMetric
Quantified metrics from difference waves.
-   **Attributes**:
    -   `modality`: enum['auditory', 'visual']
    -   `peak_latency_ms`: float
    -   `mean_amplitude_uV`: float
    -   `time_window_ms`: tuple[float, float]
    -   `electrode_region`: str
    -   `reliability_alpha`: float (Cronbach's)

### 3. CorticalSource
Localized source strength.
-   **Attributes**:
    -   `region`: str (e.g., 'Heschl's Gyrus')
    -   `source_strength`: float
    -   `coordinates`: tuple[float, float, float] (MNI)
    -   `smoothing_sigma_mm`: float

### 4. StatisticalResult
Results of hypothesis testing.
-   **Attributes**:
    -   `test_type`: str (t-test, permutation)
    -   `p_value_raw`: float
    -   `p_value_corrected`: float (BH)
    -   `decision`: enum['reject', 'fail_to_reject']
    -   `effect_size`: float (Cohen's d)

## File Formats

### Raw Data (Downloaded)
-   Format: BIDS (`.edf`, `.fif`, `.ds`).
-   Storage: `data/raw/{dataset_id}/`
-   Integrity: `data/raw/{dataset_id}/.checksum`

### Processed Data
-   Format: HDF5 (`.h5`) or Pickle (`.pkl`) for intermediate steps.
-   Storage: `data/processed/{modality}/{subject_id}.h5`
-   Schema: `contracts/processed_signal.schema.yaml`

### Metrics & Results
-   Format: Parquet (`.parquet`) or JSON.
-   Storage: `data/results/{metric_type}.parquet`
-   Schema: `contracts/metrics.schema.yaml`, `contracts/stats.schema.yaml`

## Data Flow

1.  **Download**: Raw BIDS -> `data/raw/` (Checksummed).
2.  **Preprocess**: Raw -> `data/processed/` (Filtered, ICA, Epoched).
3.  **Extract**: Processed -> `data/results/metrics.parquet` (Latency, Amplitude).
4.  **Localize**: Processed -> `data/results/sources.parquet` (Source strength).
5.  **Stat**: Metrics + Sources -> `data/results/stats.json` (P-values, Decisions).
