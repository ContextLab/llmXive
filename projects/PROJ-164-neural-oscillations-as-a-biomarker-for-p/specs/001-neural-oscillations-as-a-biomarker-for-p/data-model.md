# Data Model: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Overview

This document defines the data structures for the pipeline, covering raw ingestion, processed features, and output artifacts. All data is stored in `data/` (raw) and `output/` (derived).

## Entities

### 1. Raw EEG Epoch
Represents a 2‑second window of filtered EEG data.
- **Subject ID**: Unique identifier.
- **Condition**: `rest` or `task`.
- **Time Series**: 2D array (Channels × Samples).
- **Metadata**: Sampling rate, channel names, reference.

### 2. tDCS Response
Represents the percentage change in motor task score.
- **Subject ID**: Matches EEG Subject ID.
- **Pre Score**: Baseline motor task performance.
- **Post Score**: Post‑stimulation motor task performance.
- **Response %**: `((Post - Pre) / Pre) * 100`.

### 3. Feature Vector (Pre-Reduction)
Aggregated metrics per subject **before dimensionality reduction**.
- **Subject ID**: Unique identifier.
- **Power Features**: Dictionary of band power (delta, theta, alpha, beta, gamma) per channel.
- **Connectivity Features**: Dictionary of PLV/wPLI per channel pair.
- **tDCS Response**: Target variable.

### 4. Feature Vector (Reduced)
Aggregated metrics per subject **after dimensionality reduction** (Phase 6).
- **Subject ID**: Unique identifier.
- **Reduced Features**: Numeric array of length `p_reduced` where `p_reduced ≤ 0.5 × N`.  
- **tDCS Response**: Target variable.

### 5. Analysis Mode
State of the system:
- `Primary Mode`: Valid single‑source paired data exists.
- `Data Insufficient Mode`: No valid paired data found.
- `Underpowered`: Valid data but `N < N_min` or `p_reduced > 0.5 * N`.

## File Formats

### `data/raw/*.edf` / `data/raw/*.bids/`
Raw EEG data in BIDS or EDF format. Unmodified.

### `data/processed/features.csv`
CSV containing the **pre‑reduction** feature matrix (spectral power + connectivity). Columns: `subject_id`, `power_delta_chX`, …, `plv_c3_c4`, `wpli_c3_c4`, `tdcs_response`.

### `data/processed/reduced_features.npy`
NumPy binary array of the **post‑reduction** feature matrix (after PCA or LASSO). Shape `(N, p_reduced)` where `p_reduced ≤ 0.5 × N`. This constraint guarantees that the subsequent regression model satisfies the `p ≤ 0.5 × N` rule, mitigating the p ≫ n problem highlighted in the review.

### `output/verified_source_manifest.json`
JSON artifact listing search results (see FR‑017, FR‑018).

### `output/pre-registration.json`
JSON artifact generated before any processing (see FR‑016).

### `output/results.json`
Final statistical output (only in Primary Mode). See `contracts/output.schema.yaml`.

## Constraints

- **Memory**: Feature matrices are chunked; if `N` is large, down‑sample epochs to stay within 7 GB RAM.  
- **Precision**: All floating‑point values stored as `float64`.  
- **Integrity**: Raw data checksums must match entries in `state/...yaml` `artifact_hashes`.  
- **Dimensionality**: After Phase 6, `p_reduced` must satisfy `p_reduced ≤ 0.5 × N`. If this cannot be achieved, the pipeline flags **Underpowered** and aborts modeling (FR‑008).