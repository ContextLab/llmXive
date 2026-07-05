# Data Model: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

## Overview

This document defines the data structures used in the pipeline. All data is derived from the `ds000277` dataset and processed according to the fMRIPrep 23.1.3 and Schaefer 400 standards.

## Entities

### 1. Participant
Unique identifier linking imaging and behavioral data.
- `participant_id`: String (e.g., "sub-001")
- `age`: Integer
- `sex`: String ("M", "F", "Other")
- `baseline_wm_score`: Float (Working Memory Score)
- `mean_fd`: Float (Mean Framewise Displacement)
- `excluded_motion`: Boolean (True if mean_fd > 3.0)
- `excluded_missing_wm`: Boolean (True if WM score is missing)

### 2. ConnectivityMatrix
Symmetric 400x400 matrix.
- `participant_id`: String
- `matrix_data`: List[List[Float]] (Flattened or 2D array)
- `parcellation`: String ("Schaefer400")
- `distance_metric`: String ("Pearson")

### 3. NetworkMetrics
Aggregated graph properties.
- `participant_id`: String
- `global_efficiency`: Float
- `modularity`: Float (Q)
- `frontoparietal_strength`: Float
- `default_mode_strength`: Float

### 4. RegressionResult
Output of the statistical model.
- `predictor`: String
- `coefficient`: Float
- `std_error`: Float
- `p_value_raw`: Float
- `p_value_adjusted`: Float (Holm-Bonferroni)
- `ci_lower`: Float
- `ci_upper`: Float
- `significant`: Boolean

### 5. PipelineLog
JSON log of pipeline execution.
- `exclusion_motion`: Integer (Count of excluded due to motion)
- `exclusion_missing_wm`: Integer (Count of excluded due to missing WM)
- `runtime`: Float (Seconds)
- `id_validation_status`: String ("PASS" or "FAIL")
- `dataset_source`: String (URL or identifier)

## Data Flow

1.  **Raw Data**: `ds000277` (NIfTI, JSON, TSV).
2.  **Preprocessed**: fMRIPrep outputs (cleaned NIfTI, confounds TSV).
3.  **Metrics**: `baseline_metrics.csv` (Participant + NetworkMetrics).
4.  **Behavioral**: `baseline_wm_scores.csv` (Participant + WM + Demographics).
5.  **Joined**: `analysis_dataset.csv` (Combined for regression).
6.  **Results**: `model_summary.csv`, `effect_sizes.pdf`, `pipeline_log.json`.

## Constraints

- **Missing Data**: Participants with missing `mean_fd` or `baseline_wm_score` are excluded.
- **Motion**: Participants with `mean_fd > 3.0` are excluded (Constitution Override).
- **ID Validation**: Every participant in `baseline_metrics.csv` must exist in `baseline_wm_scores.csv`.
- **Variable Verification**: The `baseline_wm_score` column must exist in behavioral data; otherwise, the pipeline halts.