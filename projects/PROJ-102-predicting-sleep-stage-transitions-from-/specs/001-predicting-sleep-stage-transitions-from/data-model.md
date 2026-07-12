# Data Model: Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning

## Overview

This document defines the data structures, schemas, and relationships for the project. It ensures that all data artifacts (raw, processed, features, models) are consistently formatted and traceable.

## Entities

### 1. Raw Data (Sleep-EDF SC)
- **Source**: PhysioNet (`sleep-edfx` SC subset).
- **Format**: `.edf` (European Data Format).
- **Fields**:
  - `subject_id`: String (e.g., "SC001")
  - `eeg_fpz_cz`: Float array (samples)
  - `eog_left`, `eog_right`: Float arrays (for validation)
  - `emg`: Float array (for validation)
  - `hypnogram`: Integer array (30s epochs, encoded 0-4)

### 2. Preprocessed Epoch
- **Derived From**: Raw Data.
- **Type**: `EEG_Epoch` (30s) or `Transition_Window` (60s).
- **Fields**:
  - `epoch_id`: String (unique hash)
  - `subject_id`: String
  - `start_time`: Float (seconds from start of recording)
  - `duration`: Int (30 or 60)
  - `label`: Int (Sleep Stage)
  - `is_transition`: Boolean
  - `eeg_data`: Float array (filtered, normalized)
  - `metadata`: JSON (interpolation flags, filter params)

### 3. Feature Vector
- **Derived From**: Preprocessed Epoch.
- **Fields**:
  - `feature_id`: String (unique hash)
  - `epoch_id`: String (FK)
  - `time_features`: JSON (RMS, ZeroCrossing)
  - `freq_features`: JSON (Delta, Theta, Alpha, Sigma, Beta power)
  - `nonlinear_features`: JSON (SampleEntropy, DFA)
  - `label`: Int (Sleep Stage)
  - `is_transition`: Boolean

### 4. Model Output
- **Derived From**: Feature Vector (Sequence).
- **Fields**:
  - `prediction_id`: String
  - `input_sequence_id`: String
  - `predicted_prob_transition`: Float (0.0 - 1.0)
  - `actual_label`: Int
  - `is_correct`: Boolean

## Data Flow

1. **Download**: `Raw Data` → `data/raw/` (`.edf` files).
2. **Preprocess**: `Raw Data` → `data/processed/` (`.npy` or `.parquet` for epochs).
3. **Feature Extraction**: `Preprocessed Epoch` → `data/processed/features.parquet`.
4. **Statistical Test**: `Feature Vector` → `data/interim/stats_results.json`.
5. **Model Training**: `Feature Vector` → `data/models/checkpoint.pth`.
6. **Validation**: `Model Output` → `data/interim/metrics.json`.

## Constraints & Validation

- **Integrity**: All derived files must reference the `subject_id` and `epoch_id` of the source.
- **Immutability**: Raw data files are never overwritten.
- **Schema Compliance**: All processed data must conform to the schemas defined in `contracts/`.
