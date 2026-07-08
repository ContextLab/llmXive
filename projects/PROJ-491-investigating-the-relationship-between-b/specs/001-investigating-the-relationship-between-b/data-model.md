# Data Model: Investigating the Relationship Between Brain Network Dynamics and Anticipatory Reward Processing

## 1. Overview

This document defines the data structures used throughout the pipeline: from raw ingestion to final reporting. All data is stored in standard formats (NIfTI, CSV, JSON) to ensure interoperability and reproducibility.

## 2. Data Entities

### 2.1 Subject
Represents a single participant in the HCP dataset.
- **Attributes**:
  - `subject_id`: Unique identifier (string).
  - `session_id_rest`: Session ID for resting-state scan (string).
  - `session_id_task`: Session ID for task-fMRI scan (string).
  - `status`: "valid", "skipped_missing_data", "skipped_same_session", "skipped_zero_variance".

### 2.2 Time Series
Extracted BOLD signal for a specific ROI or atlas node.
- **Format**: CSV (one row per time point, one column per ROI/node).
- **Columns**: `timepoint`, `node_1`, `node_2`, ..., `vs_roi`.
- **Dimensions**: `T x N` (Time points x Nodes).

### 2.3 Dynamic Connectivity State Sequence
Sequence of cluster assignments for each time point.
- **Format**: CSV (one row per time point).
- **Columns**: `timepoint`, `state_id` (integer 0-3).

### 2.4 Flexibility Score
Scalar metric for a subject.
- **Attributes**:
  - `subject_id`: String.
  - `flexibility_score`: Float (transitions per window).
  - `window_size`: Integer (e.g., 30).

### 2.5 Reward Activation
Scalar metric for a subject.
- **Attributes**:
  - `subject_id`: String.
  - `vs_activation`: Float (mean BOLD signal change in VS during reward cue).

### 2.6 Correlation Result
Output of the statistical analysis.
- **Attributes**:
  - `window_size`: Integer.
  - `r`: Float (Pearson coefficient).
  - `p_raw`: Float (raw p-value).
  - `p_perm`: Float (empirical p-value from permutation).
  - `n_subjects`: Integer (number of subjects included).

### 2.7 Final Report
Markdown document containing all results.
- **Structure**:
  - Header (Title, Date).
  - Methods (Summary of pipeline).
  - Results (Table of correlations, Plot image).
  - Interpretation (Strictly "associational").

## 3. File Paths & Storage

| File | Path | Description |
|------|------|-------------|
| Raw NIfTI (Rest) | `data/raw/{subject_id}_rest.nii.gz` | Resting-state fMRI. |
| Raw NIfTI (Task) | `data/raw/{subject_id}_task.nii.gz` | Task-fMRI. |
| Time Series CSV | `data/processed/{subject_id}_timeseries.csv` | Extracted BOLD signals. |
| State Sequence CSV | `data/processed/{subject_id}_states.csv` | K-means cluster assignments. |
| Flexibility Scores | `data/processed/flexibility_scores.csv` | Aggregated scores per subject. |
| Activation Scores | `data/processed/activation_scores.csv` | Aggregated VS activation per subject. |
| Results CSV | `data/processed/correlation_results.csv` | Final statistical outputs. |
| Report | `paper/results.md` | Final markdown report. |

## 4. Data Flow

1.  **Ingestion**: Raw NIfTI downloaded to `data/raw/`.
2.  **Preprocessing**: NIfTI -> CSV (Time Series) in `data/processed/`.
3.  **Connectivity**: Time Series -> State Sequence -> Flexibility Score.
4.  **Analysis**: Flexibility + Activation -> Correlation Result.
5.  **Reporting**: Results -> Markdown Report.
