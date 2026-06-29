# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

## Entity Relationship Overview

The data model consists of three primary entities: `Subject`, `ConnectivityMatrix`, and `CorrelationResult`.

### Subject
Represents a single participant.
- **Attributes**: `subject_id` (str), `age` (int), `sex` (str), `motor_task_score` (float), `fd_mean` (float), `tSNR` (float).
- **Constraints**: `subject_id` is unique. `motor_task_score` and `fd_mean` must be non-null for inclusion in analysis.

### ConnectivityMatrix
Represents the functional connectivity for a subject.
- **Attributes**: `subject_id` (str), `matrix_data` (numpy array, 400x400), `modularity` (float), `global_efficiency` (float), `participation_coef_mean` (float), `within_module_degree_mean` (float).
- **Constraints**: `matrix_data` must be symmetric. Diagonal is zero.

### CorrelationResult
Stores the outcome of the statistical test.
- **Attributes**: `metric_name` (str), `r_value` (float), `p_value` (float), `q_value` (float), `significant` (bool), `covariate_controlled` (bool), `ci_lower` (float), `ci_upper` (float), `n_subjects` (int).
- **Constraints**: `q_value` is the FDR-corrected p-value. `significant` is true if `q_value < 0.05`. `ci_lower` and `ci_upper` are the 95% Confidence Intervals.

## File Formats

### Raw Data (Downloaded)
- **Format**: NIfTI (`.nii.gz`) for fMRI, CSV/JSON for behavioral data.
- **Location**: `data/raw/`

### Processed Data
- **Format**: HDF5 (`.h5`) for connectivity matrices and metrics.
- **Location**: `data/processed/`

### Analysis Results
- **Format**: CSV (`.csv`) for correlation results, JSON (`.json`) for confidence intervals.
- **Location**: `data/analysis/`

## Data Flow

1. **Download**: Raw NIfTI and behavioral CSVs fetched from HCP API (or verified ICA-FIX parquet fallback).
2. **Preprocess**: Raw NIfTI -> Cleaned NIfTI (motion corrected, normalized) - *Fallback only*.
3. **Extract**: Cleaned NIfTI -> Time Series -> **Motion Regression** -> Connectivity Matrix (400x400) -> Network Metrics.
4. **Analyze**: Network Metrics + Behavioral Scores -> PCA/MANOVA -> Correlation Results (with FDR and 95% CI).
5. **Visualize**: Correlation Results -> Scatter Plots, Network Diagrams.
6. **Report**: All results -> Markdown/PDF Report (including Limitation Statement).