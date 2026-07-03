# Data Model: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## Entity Relationship Overview

The data model is designed to support trial-level analysis, subject-level random effects, and artifact traceability.

### Core Entities

1.  **Subject**: Represents a participant in the study.
2.  **Trial**: Represents a single visual search attempt.
3.  **PupilSample**: Time-series data points for pupil diameter.
4.  **FeatureSet**: Aggregated metrics per trial (peak, mean, etc.).
5.  **ModelResult**: Outputs from statistical models.
6.  **QualityReport**: Exclusion logs and data hygiene metrics.

## Schema Definitions

### 1. Raw Eye-Tracking Data (Unaltered)
*Source*: `data/raw/` (OpenNeuro files)
*Format*: `.edf`, `.csv`, or `.parquet` (if converted)
*Schema*:
- `subject_id`: string (e.g., "sub-01")
- `trial_id`: string (e.g., "tr-001")
- `timestamp`: float (milliseconds since trial start)
- `pupil_diameter`: float (mm)
- `x`: float (gaze x-coordinate)
- `y`: float (gaze y-coordinate)
- `event_type`: string (e.g., "fixation", "saccade")

### 2. Processed Trial Data
*Source*: `data/processed/trial_features.csv`
*Schema*:
- `subject_id`: string
- `trial_id`: string
- `search_time`: float (seconds, behavioral measure)
- `target_salience`: float (0.0-1.0, computed or metadata) OR null if uncomputable
- `fixation_count`: integer
- `pupil_peak`: float (max dilation in trial)
- `pupil_mean`: float (mean dilation in trial)
- `pupil_std`: float (std deviation)
- `blink_loss_pct`: float (percentage of samples interpolated/excluded)
- `exclusion_flag`: boolean (True if trial excluded due to >30% loss or timestamp error)
- `lag_optimal`: float (optimal time lag in seconds, e.g., 1.0)

### 3. Correlation Results
*Source*: `results/correlations.csv`
*Schema*:
- `pupil_metric`: string (e.g., "pupil_peak")
- `load_proxy`: string (e.g., "search_time")
- `pearson_r`: float
- `p_value_raw`: float
- `p_value_fdr`: float (Benjamini-Hochberg adjusted)
- `significant`: boolean (True if p_value_fdr < 0.05)
- `status`: string (e.g., "COMPLETED", "UNFULFILLABLE")

### 4. LME Model Summary
*Source*: `results/model_summary.csv`
*Schema*:
- `predictor`: string (e.g., "search_time")
- `estimate`: float
- `std_error`: float
- `z_value`: float
- `p_value`: float
- `vif`: float (Variance Inflation Factor)
- `model_fit_stat`: string (e.g., "AIC", "BIC", "Likelihood Ratio")

### 5. Classification Metrics
*Source*: `results/classification_metrics.csv`
*Schema*:
- `threshold`: float (0.40, 0.50, 0.60)
- `accuracy`: float
- `precision`: float
- `recall`: float
- `roc_auc`: float
- `confusion_matrix`: string (JSON encoded: [[TN, FP], [FN, TP]])
- `ground_truth_limitation`: string (e.g., "Search-Time Estimation (Self-Validated)" or "Independent Measure")

### 6. Quality Report
*Source*: `results/quality_report.csv`
*Schema*:
- `exclusion_type`: string (e.g., "blink_loss", "timestamp_error", "insufficient_trials")
- `count`: integer
- `percentage`: float

## Data Flow

1.  **Ingest**: Raw files -> `data/raw/`
2.  **Preprocess**: Raw -> Filtered/Interpolated -> `data/processed/trial_features.csv` (via MNE-to-CSV conversion)
3.  **Align**: Apply time-lags -> `data/processed/trial_features_lagged.csv`
4.  **Analyze**: `trial_features_lagged.csv` -> `correlations.csv`, `model_summary.csv`
5.  **Classify**: `trial_features_lagged.csv` -> `classification_metrics.csv`
6.  **Report**: All results -> `quality_report.csv`, `state/project_state.yaml`

## Constraints & Validations

- **Timestamps**: Must be strictly increasing within a trial.
- **Pupil Diameter**: Must be > 0.
- **Search Time**: Must be > 0.
- **Exclusion**: Trials with `blink_loss_pct` > 0.30 are flagged and excluded from analysis.
- **Collinearity**: If `vif` > 5 for any predictor, the model is refit without that predictor.
- **Uncomputable Proxy**: If `target_salience` is null due to missing images, `status` in correlation results MUST be "UNFULFILLABLE".