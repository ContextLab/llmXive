# Data Model: Examining the Impact of Auditory Feedback on Motor Sequence Learning

## Overview

This document defines the data structures, file formats, and schemas used throughout the pipeline. All data adheres to the BIDS (Brain Imaging Data Structure) specification for raw and preprocessed neuroimaging data.

## Data Entities

### 1. Raw Dataset (BIDS)
- **Source**: OpenNeuro `ds000115`.
- **Format**: BIDS (NIfTI + JSON + TSV).
- **Key Files**:
  - `sub-<label>/func/sub-<label>_task-motor_run-<label>_bold.nii.gz`: Raw fMRI data.
  - `sub-<label>/func/sub-<label>_task-motor_run-<label>_events.tsv`: Event logs (onset, duration, trial_type).
  - `sub-<label>/func/sub-<label>_task-motor_run-<label>_events.json`: Event metadata.

### 2. Preprocessed Data (fmriprep)
- **Output Directory**: `data/processed/sub-<label>/func/`.
- **Key Files**:
  - `sub-<label>_desc-preproc_bold.nii.gz`: Preprocessed BOLD image.
  - `sub-<label>_desc-confounds_timeseries.tsv`: Motion parameters and other confounds.
  - `sub-<label>_space-MNI_desc-preproc_bold.nii.gz`: Normalized BOLD image.

### 3. GLM Outputs
- **Format**: NIfTI (`.nii.gz`) and JSON (`.json`).
- **Key Files**:
  - `sub-<label>_contrast-perturbed_vs_normal.nii.gz`: Contrast map.
  - `sub-<label>_contrast-perturbed_vs_normal_t-stat.nii.gz`: T-statistic map.
  - `sub-<label>_design_matrix.tsv`: Design matrix used in GLM.

### 4. Behavioral Metrics
- **Format**: CSV (`data/processed/behavioral_metrics.csv`).
- **Columns**: `subject_id`, `condition`, `mean_rt`, `accuracy`, `std_rt`.

### 5. Statistical Results
- **Format**: JSON/YAML (`data/processed/stats_results.json`).
- **Structure**: Group-level t-test results, cluster coordinates, p-values, effect sizes.

### 6. Power Analysis
- **Format**: JSON/YAML (`data/processed/power_analysis.json`).
- **Structure**: Observed power, sample size, effect size, threshold, limitations.

## Data Flow

1. **Download**: `code/download_data.py` → `data/raw/ds000115/` (BIDS).
2. **Verify**: `code/verify_conditions.py` → Checks for required conditions; halts if missing.
3. **Preprocess**: `code/run_fmriprep.sh` → `data/processed/` (Preprocessed NIfTI).
4. **GLM**: `code/preprocess_glms.py` → `data/processed/` (Contrast Maps).
5. **Group Analysis**: `code/group_analysis.py` → `data/processed/` (Group Stats).
6. **Null Test**: `code/null_test.py` → `data/processed/` (Permutation results).
7. **Correlation**: `code/brain_behavior.py` → `data/processed/` (Scatter data).
8. **Power**: `code/power_analysis.py` → `data/processed/` (Power report).

## Data Validation

- **BIDS Validator**: Raw data must pass `bids-validator`.
- **File Existence**: Pipeline checks for existence of expected files before proceeding.
- **Checksums**: MD5 checksums of raw data stored in `state/...yaml`.