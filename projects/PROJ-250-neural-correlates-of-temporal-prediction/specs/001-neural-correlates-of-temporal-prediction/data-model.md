# Data Model: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Overview

This data model ensures traceability from raw EEG signals to statistical conclusions, adhering to the project's **Single Source of Truth** principle.

## Core Entities

### 1. EEG Dataset (Input)
Represents the raw BIDS-formatted data.
- `dataset_id`: String (e.g., "ds004510").
- `raw_file_hash`: String (SHA-256).
- `subjects`: List of Subject IDs.

### 2. Subject (Metadata)
- `subject_id`: String (Unique identifier).
- `is_excluded`: Boolean (True if >50% epochs rejected).
- `exclusion_reason`: String (Optional).
- `artifact_rejection_rate`: Float (Percentage of rejected epochs).

### 3. Epoch (Processed Signal)
- `epoch_id`: String (Unique identifier).
- `subject_id`: String (Foreign Key).
- `condition_label`: Enum ("simple", "complex").
- `stimulus_type`: Enum ("standard", "deviant").
- `signal_data`: Array (Channels $\times$ Timepoints).
- `time_window`: Range ([-0.2, 0.5] seconds).
- `baseline_corrected`: Boolean (True if pre-stimulus mean [-200, 0]ms subtracted).

### 4. MMN Metric (Aggregated Result)
The primary unit of analysis, aggregating signal data into quantitative metrics.
- `metric_id`: String.
- `subject_id`: String (Foreign Key).
- `electrode`: String (e.g., "Fz").
- `condition_label`: Enum ("simple", "complex").
- `amplitude_diff`: Float ($\mu$V, Deviant - Standard).
- `latency_diff`: Float (ms).
- `snr_ratio`: Float (|Amplitude| / SEM of pre-stimulus baseline).
- `signal_validity`: Boolean ($\text{SNR} \ge 3.0$).
- `t_statistic`: Float.
- `p_value_fdr`: Float (FDR-corrected).
- `cohen_d`: Float.
- `practical_significance`: Boolean ($\text{Cohen's } d \ge 0.5$).
- `topographic_correlation`: Float (Pearson $r$ vs. canonical template).
- `validation_type`: Enum ("consistency_simple", "validity_complex") (Distinguishes whether this is a consistency check on simple or validity check on complex).
- `significant`: Boolean ($p < 0.05$).

## Data Flow & Transformations

1. **Raw $\to$ Processed**: `download.py` $\to$ `preprocess.py`. Raw BIDS files are filtered, ICA-cleaned, baseline-subtracted, and epoched into `.fif` files.
2. **Processed $\to$ Metrics**: `analysis.py` computes mean differences in the 150–250ms window for each subject/electrode/condition.
3. **Metrics $\to$ Statistics**: `analysis.py` performs paired t-tests across the subject cohort and applies FDR correction.
4. **Statistics $\to$ Output**: Final results are written to `results/metrics.csv` and `results/stats.json`.

## Constraints

- **Temporal Constraint**: All epoch data must be strictly within the -200ms to 500ms window.
- **Baseline Correction Constraint**: Every epoch must have the pre-stimulus baseline (-200ms to 0ms) mean subtracted before analysis.
- **Integrity Constraint**: `signal_validity` must be True for any result claimed as a "detected MMN".
- **Independence Constraint**: `condition_label` must be an independent variable in the dataset metadata, not derived from `stimulus_type`.
- **Topographic Validation Constraint**: `validation_type` must distinguish between consistency checks (simple vs. template) and validity checks (complex vs. template) to avoid circular reasoning.
