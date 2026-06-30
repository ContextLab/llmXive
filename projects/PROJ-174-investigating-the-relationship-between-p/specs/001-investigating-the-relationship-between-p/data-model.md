# Data Model: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## Overview

This document defines the data structures, schemas, and transformation rules used in the pipeline. All data files are stored in CSV format for portability and ease of inspection. The model adheres to the project constitution's Data Hygiene and Versioning requirements.

## Entity Definitions

### 1. Raw Trial Data (`data/raw/`)
- **Source**: OpenNeuro ds004248 (or a user‑provided compatible dataset).
- **Format**: `.edf` (raw) or `.csv` (converted).
- **Schema**:
  - `subject_id`: String (Participant ID)
  - `trial_id`: Integer (Trial index)
  - `timestamp`: Float (Milliseconds relative to stimulus onset)
  - `x`: Float (Horizontal gaze position, degrees or pixels)
  - `y`: Float (Vertical gaze position, degrees or pixels)
  - `pupil_diameter`: Float (mm or arbitrary units)
  - `event_type`: String (e.g., "stimulus_onset", "response")
  - `response_time`: Float (ms, if available)

### 2. Processed Trial Data (`data/processed/`)
- **Derivation**: Preprocessed from Raw Data (blink interpolation, filtering, baseline correction, trial alignment).
- **Format**: `.csv`
- **Schema**:
  - `subject_id`: String
  - `trial_id`: Integer
  - `pupil_peak`: Float (Max dilation in trial)
  - `pupil_mean`: Float (Mean dilation in trial)
  - `pupil_quantiles`: String (JSON string of quantiles [0.1, 0.5, 0.9])
  - `search_time`: Float (ms, from behavioral response)
  - `stimulus_salience`: Float (Provided by stimulus metadata; null if unavailable)
  - `fixation_count`: Integer
  - `is_excluded`: Boolean (True if >30 % missing data or timestamp error)
  - `exclusion_reason`: String (e.g., "blink_loss", "timestamp_error")
  - `load_label`: Integer (1 = high load, 0 = low load; derived from median split of `search_time` if no independent label exists)

### 3. Analysis Results (`outputs/`)
- **Derivation**: Computed from Processed Trial Data.
- **Format**: `.csv`, `.json`
- **Schema (Correlations)**:
  - `pupil_metric`: String (peak, mean, or quantile)
  - `load_proxy`: String (search_time, stimulus_salience, fixation_count)
  - `pearson_r`: Float
  - `p_value_raw`: Float
  - `p_value_adjusted`: Float (Bonferroni)
  - `significant`: Boolean
- **Schema (LME Model)**:
  - `predictor`: String
  - `estimate`: Float
  - `std_error`: Float
  - `p_value`: Float
  - `t_statistic`: Float
- **Schema (Classifier)**:
  - `threshold`: Float (Decision threshold)
  - `accuracy`: Float
  - `precision`: Float
  - `recall`: Float
  - `roc_auc`: Float
  - `confusion_matrix`: String (JSON)
  - `validation_type`: String ("Independent" or "Internal Consistency")

## Transformation Rules

1. **Blink Interpolation**:
   - Identify gaps in `pupil_diameter` > 50 ms.
   - Linear interpolation for gaps < 200 ms.
   - Exclude trial if total interpolated samples > 30 % of trial duration.

2. **Low‑Pass Filtering**:
   - Apply 4th‑order Butterworth filter with cutoff 4 Hz.
   - Pad edges with the trial mean to avoid edge artifacts.

3. **Salience Handling**:
   - `stimulus_salience` is read **only** from stimulus metadata files (e.g., `.npy`, `.json`).
   - If the metadata file is missing, `stimulus_salience` is set to null, and salience‑related analyses are **skipped**. No on‑the‑fly computation from fixation data is performed.

4. **Ground‑Truth Labeling**:
   - If an independent load measure exists, `load_label` is derived from it.
   - If not, `load_label` = 1 if `search_time` > median(`search_time`) within the dataset, else 0. This is explicitly flagged as "Internal Consistency" in the output.

5. **VIF Calculation & Collinearity Mitigation**:
   - Compute VIF for `search_time`, `stimulus_salience`, `fixation_count`.
   - If any VIF > 5, fit a **Reduced Model** by dropping the predictor with the highest VIF. PCA is excluded from the primary analysis.

## Data Quality Checks

- **Timestamp Monotonicity**: Verify `timestamp` is strictly increasing within each trial; non‑monotonic trials are excluded with reason `timestamp_error`.
- **Physiological Range**: `pupil_diameter` must be within 2 mm – 8 mm; out‑of‑range values trigger exclusion.
- **Completeness**: Ensure each trial has a unique (`subject_id`, `trial_id`) pair; duplicate rows cause an error.