# Data Model: Bayesian Nonparametrics for Anomaly Detection in Time Series

## 1. Data Flow Architecture

```mermaid
graph TD
    A[Raw Data (UCI/PhysioNet/Synthetic)] --> B[Preprocessing (Normalization)]
    B --> C[Sliding Window Extraction]
    C --> D[DP-GMM Inference (ADVI)]
    C --> E[Baseline Models (GMM/ARIMA)]
    D --> F[Posterior Trajectory ($\alpha, \pi$)]
    E --> G[Reconstruction Errors (MSE)]
    F --> H[Dynamic Signatures ($\dot{\alpha}, \text{Var}(\pi)$)]
    G --> I[Time-to-Detection]
    H --> I
    I --> J[Statistical Testing (Wilcoxon, KS, Bootstrap, Survival)]
    J --> K[Reports & Artifacts]
```

## 2. Entity Definitions

### 2.1 TimeSeriesWindow
- **Description**: A contiguous slice of univariate time series data.
- **Attributes**:
  - `window_id`: Integer (unique per window).
  - `start_index`: Integer (start index in original series).
  - `end_index`: Integer (end index).
  - `data`: Array[float] (normalized values).
  - `is_anomaly`: Boolean (ground truth label if injection exists).

### 2.2 PosteriorTrajectory
- **Description**: Time-series of posterior estimates for DP-GMM parameters.
- **Attributes**:
  - `window_id`: Integer.
  - `alpha_mean`: Float (posterior mean of concentration parameter).
  - `alpha_deriv`: Float (first derivative of $\alpha$).
  - `pi_variance`: Float (variance of component weights).
  - `elbo_score`: Float (convergence metric).
  - `converged`: Boolean.

### 2.3 DetectionEvent
- **Description**: Record of an anomaly detection event.
- **Attributes**:
  - `method`: String ("DPGMM", "GMM_k3", "ARIMA").
  - `injection_timestamp`: Integer (ground truth).
  - `detection_timestamp`: Integer (first threshold crossing).
  - `time_to_detection`: Integer (steps).
  - `threshold_value`: Float.
  - `censored`: Boolean (True if no detection occurred).

### 2.4 SensitivityReport
- **Description**: Results of threshold sensitivity analysis.
- **Attributes**:
  - `threshold`: Float.
  - `false_positive_rate`: Float.
  - `false_negative_rate`: Float.
  - `stability_flag`: Boolean (true if error rates spike).

### 2.5 DatasetSplit
- **Description**: Train/Validation/Test split configuration (FR-019).
- **Attributes**:
  - `train_indices`: Array[Integer].
  - `val_indices`: Array[Integer].
  - `test_indices`: Array[Integer].

## 3. File Formats

### 3.1 Input
- **Raw Data**: CSV or Parquet (unverified sources rejected).
- **Config**: YAML (validated against schema).

### 3.2 Intermediate
- **Windows**: Parquet (`data/processed/windows.parquet`).
- **Posterior Trajectory**: Parquet (`data/processed/posterior_trajectory.parquet`).
- **Split Indices**: JSON (`data/processed/split_indices.json`).

### 3.3 Output
- **Results**: JSON (`data/processed/results/detection_report.json`).
- **Plots**: PNG (`data/processed/results/figures/`).
- **State**: YAML (`state/projects/PROJ-024-...yaml`).

## 4. Validation Rules

- **Minimum Observations**: ≥1,000 (FR-001).
- **Normalization**: Zero mean, unit variance.
- **Convergence**: ELBO delta < 0.01 (FR-009).
- **Sample Size**: If anomalies < 10, use bootstrap (FR-011).
- **Config Size**: <2KB (FR-009).
- **Data Split**: Train/Val/Test split must be defined before threshold selection (FR-019).