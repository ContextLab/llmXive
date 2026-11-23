# Data Model: Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG

## Overview

This document defines the data entities, schemas, and relationships used throughout the project. All data flows from raw BIDS files to processed APF estimates and finally to statistical model outputs.

## Entity Relationship Diagram (Conceptual)

```text
[OpenNeuro Dataset] (ds003865, ds003392, ds003775)
       |
       v
[Raw BIDS Data] (subject_id, session_id, task, run, eeg files)
       |
       +---> [Preprocessed Data A] (Pipeline A)
       |
       +---> [Preprocessed Data B] (Pipeline B)
       |
       v
[APF Estimates] (subject_id, dataset, pipeline, method, value, status)
       |
       v
[Model Outputs] (Variance Components, R², Confidence Intervals)
```

## Data Entities

### 1. Raw Dataset Metadata
Derived from BIDS `participants.tsv` and `dataset_description.json`.
*   **Fields**: `dataset_id`, `subject_id`, `session_id`, `task`, `run`, `sampling_frequency`, `channel_count`, `file_path`.

### 2. Preprocessed Signal (Derivative)
Stored as HDF5 or NPY arrays to save space, indexed by subject/pipeline.
*   **Fields**: `subject_id`, `pipeline_id` (A/B), `time_vector`, `signal_matrix` (channels x time), `rejection_status` (ICA components removed).

### 3. APF Estimate (Core Analysis Data)
The primary output of the estimation phase. One row per subject per pipeline per method.
*   **Fields**:
    *   `subject_id`: String (e.g., "sub-001")
    *   `dataset_id`: String (e.g., "ds003865")
    *   `pipeline_id`: String ("A" or "B")
    *   `method_id`: String ("psd" or "autocorr")
    *   `apf_value`: Float (Hz)
    *   `status`: String ("Valid", "Indeterminate", "Out-of-Band")
    *   `band_range`: String ("8-13")
    *   `accuracy_error`: Float (Hz) - *New*: Error from synthetic ground truth (if applicable)

### 4. Variance Components (Model Output)
Aggregated results from the Mixed-Effects model.
*   **Fields**:
    *   `component`: String ("dataset_source", "pipeline_type", "estimation_method", "subject", "residual")
    *   `variance_estimate`: Float
    *   `proportion`: Float (R² contribution)
    *   `ci_lower_95`: Float
    *   `ci_upper_95`: Float

### 5. Sensitivity Analysis Output
*   **Fields**:
    *   `lower_bound`: Float
    *   `upper_bound`: Float
    *   `mean_apf`: Float
    *   `delta_mean_apf`: Float (Change from baseline 8-13)

## File Formats

| File Type | Format | Location | Description |
| :--- | :--- | :--- | :--- |
| Raw Data | BIDS (EDF/VHDR) | `data/raw/{dataset_id}/` | Original downloads, checksummed. |
| Preprocessed | HDF5 | `data/derivatives/{dataset_id}_{pipeline}.h5` | Filtered/Re-referenced data. |
| APF Results | CSV | `data/processed/apf_estimates.csv` | Flat table for modeling. |
| Sensitivity | CSV | `data/processed/sensitivity_analysis.csv` | Band sweep results. |
| Model Results | JSON | `data/processed/model_results.json` | Variance components and CIs. |
| Plots | PNG | `data/processed/plots/` | Forest plots, bar charts. |

## Data Flow Constraints

1.  **Immutability**: Raw data in `data/raw` is never modified.
2.  **Derivation**: Preprocessed files are named with a hash of the pipeline parameters to ensure reproducibility.
3.  **Completeness**: If a subject is missing in Pipeline A, a row with `status="Missing"` is not created; the subject is only processed if data exists.
4.  **Out-of-Band**: Subjects with APF < 8 or > 13 are recorded with `status="Out-of-Band"` and excluded from the primary `apf_value` mean calculation but included in the "Indeterminate" count.

## Schema Validation

All CSV and JSON outputs must conform to the schemas defined in `contracts/`. The `code/` pipeline includes a validation step before writing final results.