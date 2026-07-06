# Data Model: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

## Overview

This document defines the data structures, schemas, and relationships for the project. It ensures that data flows correctly from ingestion to statistical output, adhering to the "Single Source of Truth" principle.

## Entity-Relationship Diagram (Textual)

```text
[Raw Dataset] --> [Preprocessed EEG] --> [Epochs] --> [MMN Amplitudes (Lagged)]
                                                    |
[Behavioral Logs] --> [Learning Blocks] -----------> [Aligned Data] --> [LME Output]
```

## Data Entities

### 1. Raw Dataset Metadata
- **Source**: OpenNeuro / HuggingFace
- **Fields**: `dataset_id`, `subject_id`, `task_type`, `stimulus_type`, `response_correctness`, `trial_count`, `underpowered_flag`, `analysis_mode` (error_signal | stimulus_driven).

### 2. Preprocessed EEG
- **Source**: `data/preprocess.py`
- **Fields**: `subject_id`, `channel`, `time`, `amplitude`, `ica_components_removed`, `bad_channels_interpolated`.
- **Format**: HDF5 or MNE Epochs object (serialized to `.fif` or `.npy`).

### 3. Aligned Data (Lagged)
- **Source**: `data/align.py`
- **Fields**: 
  - `subject_id`: Unique identifier.
  - `mmn_source_block_id`: ID of the block from which MMN was derived (trials t-50 to t-10).
  - `accuracy_target_block_id`: ID of the block for which accuracy is calculated (trials t to t+10).
  - `accuracy_pct`: Percentage of correct responses in the target block.
  - `stationarity_check`: True if accuracy trend within target block is <10%.
  - `mmn_amplitude_cp3`, `mmn_amplitude_cp4`, `mmn_amplitude_c3`, `mmn_amplitude_c4`: Mean MMN amplitude (150–250ms) from the source block.
  - `analysis_mode`: Enum ("error_signal", "stimulus_driven").
- **Format**: CSV or Parquet.

### 4. Statistical Output
- **Source**: `analysis/model.py`
- **Fields**: `model_type` (Gaussian LME), `fixed_effects`, `random_effects`, `coefficients`, `p_values`, `permutation_p_value`, `time_window`, `correction_method`, `analysis_mode`.
- **Format**: JSON or CSV.

## Data Flow

1. **Ingestion**: Raw data downloaded from verified URL. Metadata validated (Phase 0).
2. **Preprocessing**: Filtering, ICA, epoching. Output: Cleaned epochs.
3. **Alignment**: MMN calculation (lagged) + Behavioral binning. Output: Aligned CSV with explicit source/target block IDs.
4. **Modeling**: Gaussian LME fitting + Permutation. Output: Stats JSON.
5. **Reporting**: Stats JSON used to generate paper figures/tables.

## Validation Rules

- **Metadata**: `stimulus_type` and `response_correctness` must be present for "error_signal" mode.
- **Epochs**: Trial count loss ≤ 5% due to artifact rejection.
- **Blocks**: Stationarity check <10% trend.
- **Model**: Convergence check (LME must converge).
- **Schema**: All output files must validate against `contracts/` schemas.