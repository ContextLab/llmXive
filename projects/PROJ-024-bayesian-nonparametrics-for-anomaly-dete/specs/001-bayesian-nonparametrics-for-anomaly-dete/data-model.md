# Data Model: Bayesian Nonparametrics for Anomaly Detection in Time Series

## 1. Core Entities

### 1.1 TimeSeriesWindow
A sliding window of univariate data used for local distributional estimation.
- **Fields**:
  - `window_id`: Unique identifier (int).
  - `start_idx`: Start index in original series (int).
  - `end_idx`: End index in original series (int).
  - `data`: Array of normalized values (float32).
  - `timestamp`: Synthetic or real timestamp (int/float).
  - `split`: "train", "val", "test" (string).

### 1.2 PosteriorTrajectory
The time-series record of posterior means extracted from the DP-GMM.
- **Fields**:
  - `window_id`: Reference to `TimeSeriesWindow` (int).
  - `alpha_mean`: Posterior mean of local concentration parameter $\alpha_t$ (float).
  - `alpha_std`: Posterior standard deviation of $\alpha_t$ (float).
  - `pi_mean`: Component weights (array of floats).
  - `pi_var`: Variance of component weights (float).
  - `alpha_derivative`: First derivative of $\alpha_t$ (float).
  - `converged`: Boolean flag for ADVI convergence (bool).
  - `elbo_final`: Final ELBO value (float).

### 1.3 DetectionEvent
A record of an anomaly detection event.
- **Fields**:
  - `event_id`: Unique identifier (int).
  - `method`: "DP-GMM", "GMM-k3", "GMM-k5", "GMM-k10", "ARIMA" (string).
  - `detection_timestamp`: Step index of detection (int).
  - `injection_timestamp`: Ground-truth injection step (int).
  - `time_to_detection`: Steps from injection to detection (int).
  - `score`: Anomaly score at detection (float).
  - `blind_validation`: Boolean indicating if detection was blind (bool).

### 1.4 SensitivityReport
Structured output of threshold sensitivity analysis.
- **Fields**:
  - `threshold_value`: Cutoff value (float).
  - `false_positive_rate`: FP rate at this threshold (float).
  - `false_negative_rate`: FN rate at this threshold (float).
  - `stability_flag`: Boolean indicating instability (bool).

### 1.5 TraceabilityRecord
Record for tracing figures/stats to code/data (Constitution Principle IV).
- **Fields**:
  - `figure_id`: Unique identifier for the figure/stat (string).
  - `data_file_hash`: SHA256 hash of the source data file (string).
  - `code_file_path`: Relative path to the code block (string).
  - `code_line_number`: Line number in the code file (int).

## 2. Data Flow

```mermaid
graph TD
    A[Raw Data] --> B[Normalization]
    B --> C[Split: Train/Val/Test]
    C --> D[Sliding Window]
    D --> E[DP-GMM Inference]
    D --> F[Baseline Inference]
    E --> G[PosteriorTrajectory]
    F --> H[Baseline Scores]
    G --> I[Anomaly Scoring]
    H --> I
    I --> J[DetectionEvent]
    J --> K[Statistical Testing (Bootstrap)]
    K --> L[TraceabilityRecord]
    L --> M[Final Report]
```

## 3. Storage Schema

### 3.1 Input Data
- **Location**: `data/raw/`
- **Format**: CSV, JSON, Parquet (verified sources only).
- **Checksum**: SHA256 hash stored in `state/`.

### 3.2 Processed Data
- **Location**: `data/processed/`
- **Files**:
  - `normalized_data.parquet`: Normalized time series with split labels.
  - `windowed_data.parquet`: Sliding window data.
  - `posterior_trajectory.jsonl`: Posterior means and derivatives.
  - `detection_events.jsonl`: Detection records.
  - `sensitivity_report.json`: Threshold sweep results.
  - `traceability_report.json`: File hashes and code references.

### 3.3 State Files
- **Location**: `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
- **Content**:
  - `artifact_hashes`: Checksums for all data files.
  - `updated_at`: Timestamp of last change.
  - `config_hash`: Hash of `config.yaml`.
  - `generator_hash`: Hash of synthetic data generator (updated on change).

## 4. Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| `data` | Length ≥ 50 | "Window size too small (min 50)." |
| `alpha_derivative` | Not NaN | "Convergence failed." |
| `time_to_detection` | ≥ 0 | "Invalid detection timestamp." |
| `config.yaml` | Size < 2KB | "Config file too large." |
| `split` | One of ["train", "val", "test"] | "Invalid split label." |
