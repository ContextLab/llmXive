# Data Model: Alpha Oscillations and Working Memory Capacity

## Overview

This document defines the data structures used in the pipeline. All data is stored in `data/` with checksums recorded in `state/`.

## Entity Definitions

### 1. EEG Dataset (Raw)
- **Source**: OpenNeuro (BIDS format).
- **Attributes**:
  - `dataset_id`: String (e.g., "ds000248")
  - `subject_id`: String (e.g., "sub-01")
  - `sampling_rate`: Float (Hz)
  - `channels`: List of Strings (e.g., ["F3", "F4", "Fz", "P3", "P4", "Pz"])
  - `events`: DataFrame (onset, duration, trial_type)
  - `behavioral`: Dict (k_score, d_prime, accuracy)

### 2. Preprocessed Epochs (Intermediate)
- **Source**: `code/01_download_preprocess.py` output.
- **Format**: HDF5 or NPZ (compressed).
- **Attributes**:
  - `subject_id`: String
  - `trial_id`: Integer
  - `time`: Array (Float)
  - `data`: Array (Float, shape: [n_channels, n_times])
  - `condition`: String (e.g., "load_3", "load_4")

### 3. Alpha Power Metric (Derived)
- **Source**: `code/02_extract_metrics.py` output.
- **Format**: CSV / Parquet.
- **Schema**:
  - `subject_id`: String
  - `electrode`: String (F3, F4, Fz, P3, P4, Pz)
  - `condition`: String
  - `power_value`: Float (µV²/Hz)
  - `frequency_band`: String ("alpha_8_12")

### 4. PLV Metric (Derived)
- **Source**: `code/02_extract_metrics.py` output.
- **Format**: CSV / Parquet.
- **Schema**:
  - `subject_id`: String
  - `pair_id`: String (e.g., "Fz-Pz")
  - `condition`: String
  - `plv_value`: Float (0.0 to 1.0)
  - `frequency_band`: String ("alpha_8_12")

### 5. Correlation Results (Final)
- **Source**: `code/03_correlation_analysis.py` output.
- **Format**: JSON / CSV.
- **Schema**:
  - `metric_type`: String ("power", "plv", "pca_component")
  - `electrode_or_pair`: String
  - `correlation_coefficient`: Float
  - `p_value`: Float
  - `ci_lower`: Float
  - `ci_upper`: Float
  - `corrected_p`: Float (FDR)
  - `significance`: Boolean
  - `threshold_status`: String ("PASS" if |r| ≥ 0.3, else "FAIL")
  - `vif_flag`: Boolean (True if VIF > 5)

## Data Flow Diagram

```mermaid
graph TD
    A[OpenNeuro BIDS] -->|Download| B(01_download_preprocess.py)
    B -->|Validate FR-006| C{Has Behavioral?}
    C -->|No| D[HALT: ERROR]
    C -->|Yes| E[Preprocessed Epochs]
    E -->|Extract FR-003, FR-004| F[Alpha Power & PLV Metrics]
    F -->|Check Collinearity FR-009| G{VIF > 5?}
    G -->|Yes| H[PCA Components - Descriptive Only]
    G -->|No| I[Raw Metrics]
    H -->|Correlate FR-005, FR-007| J[Correlation Results]
    I -->|Correlate FR-005, FR-007| J
    J -->|Correct FR-005 (FDR)| K[Final Statistics]
    K -->|Check SC-001| L[Threshold Status]
    K -->|Check SC-002| M[Reliability Status]
```
