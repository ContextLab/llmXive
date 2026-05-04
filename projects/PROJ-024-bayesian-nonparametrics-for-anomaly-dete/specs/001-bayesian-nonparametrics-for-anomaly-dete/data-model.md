# Data Model Specification
# Bayesian Nonparametrics for Anomaly Detection in Time Series
# Version: 1.0.0
# Last Updated: 2026-05-01

## Overview

This document defines the canonical data model for the Bayesian Nonparametrics
Anomaly Detection project. All entities, schemas, and data flows are specified
here to ensure consistency across implementation, testing, and evaluation.

## Entity Definitions

### TimeSeries

Core entity representing a univariate or multivariate time series with timestamps.

```python
@dataclass
class TimeSeries:
    """
    Represents a time series with observations and metadata.
    
    Fields:
        series_id: Unique identifier for this time series
        name: Human-readable name
        observations: Array of shape (n_observations, n_features)
        timestamps: Array of shape (n_observations,) with datetime objects
        source: Dataset source (e.g., "UCI-Electricity", "Synthetic")
        start_time: First observation timestamp
        end_time: Last observation timestamp
        frequency: Sampling frequency (e.g., "1min", "1h", "1d")
        labels: Optional array of shape (n_observations,) with ground truth (0/1)
        metadata: Dict of additional properties
    """
    series_id: str
    name: str
    observations: np.ndarray  # shape: (n_obs, n_features)
    timestamps: np.ndarray    # shape: (n_obs,)
    source: str
    start_time: datetime
    end_time: datetime
    frequency: str
    labels: Optional[np.ndarray] = None  # shape: (n_obs,), 0=normal, 1=anomaly
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### TimeSeriesIterator

Streaming wrapper for sequential observation processing.

```python
@dataclass
class TimeSeriesIterator:
    """
    Iterator for streaming time series observations one at a time.
    
    Fields:
        time_series: Parent TimeSeries object
        index: Current observation index
        streaming_observation: Current StreamingObservation object
    """
    time_series: TimeSeries
    index: int = 0
    streaming_observation: Optional['StreamingObservation'] = None
```

### StreamingObservation

Single observation for streaming model updates.

```python
@dataclass
class StreamingObservation:
    """
    Single observation for streaming processing.
    
    Fields:
        timestamp: Observation timestamp
        value: Observation value(s) as ndarray
        sequence_id: Position in sequence (0-indexed)
        is_missing: Whether value contains missing data
    """
    timestamp: datetime
    value: np.ndarray  # shape: (n_features,)
    sequence_id: int
    is_missing: bool = False
```

### AnomalyScore

Output of the DPGMM model for a single observation.

```python
@dataclass
class AnomalyScore:
    """
    Anomaly score for a single observation.
    
    Fields:
        timestamp: Timestamp of the scored observation
        score: Negative log posterior probability (float)
        is_anomaly: Binary flag (0=normal, 1=anomaly)
        uncertainty: Optional uncertainty estimate (dict with variance, credible_interval)
        component_assignment: Assigned mixture component (int or None)
        sequence_id: Position in sequence
    """
    timestamp: datetime
    score: float
    is_anomaly: bool
    uncertainty: Optional[Dict[str, Any]] = None
    component_assignment: Optional[int] = None
    sequence_id: int
```

### DPGMMConfig

Configuration for the Dirichlet Process Gaussian Mixture Model.

```python
@dataclass
class DPGMMConfig:
    """
    DPGMM hyperparameters and settings.
    
    Fields:
        concentration_parameter: Dirichlet process concentration (alpha)
        n_components_max: Maximum number of mixture components
        covariance_type: 'full', 'tied', 'diag', or 'spherical'
        random_seed: Random seed for reproducibility
        elbo_tolerance: Convergence tolerance for ELBO (default: 0.001)
        max_iterations: Maximum ADVI iterations (default: 500)
        streaming_update: Whether to use streaming posterior updates
        concentration_tuning: Whether to adapt concentration parameter
        missing_value_strategy: 'skip', 'impute', 'interpolate'
    """
    concentration_parameter: float = 1.0
    n_components_max: int = 20
    covariance_type: str = 'full'
    random_seed: int = 42
    elbo_tolerance: float = 0.001
    max_iterations: int = 500
    streaming_update: bool = True
    concentration_tuning: bool = True
    missing_value_strategy: str = 'skip'
```

### EvaluationMetrics

Performance metrics for model evaluation.

```python
@dataclass
class EvaluationMetrics:
    """
    Evaluation metrics computed on test data.
    
    Fields:
        f1_score: F1 score (0-1)
        precision: Precision (0-1)
        recall: Recall (0-1)
        auc_roc: Area under ROC curve
        auc_pr: Area under PR curve
        confusion_matrix: 2x2 array [[TN, FP], [FN, TP]]
        anomaly_rate: Ratio of flagged anomalies
        runtime_seconds: Total processing time
        peak_memory_mb: Peak memory usage in MB
    """
    f1_score: float
    precision: float
    recall: float
    auc_roc: float
    auc_pr: float
    confusion_matrix: np.ndarray  # shape: (2, 2)
    anomaly_rate: float
    runtime_seconds: float
    peak_memory_mb: float
```

### DownloadResult

Result of dataset download operation.

```python
@dataclass
class DownloadResult:
    """
    Result of a dataset download operation.
    
    Fields:
        dataset_name: Name of downloaded dataset
        file_path: Path to downloaded file
        file_size_bytes: Size in bytes
        checksum_sha256: SHA256 checksum of file
        download_success: Whether download completed successfully
        error_message: Error message if download failed
    """
    dataset_name: str
    file_path: str
    file_size_bytes: int
    checksum_sha256: str
    download_success: bool
    error_message: Optional[str] = None
```

### SyntheticDataset

Generated synthetic time series with known ground truth.

```python
@dataclass
class SyntheticDataset:
    """
    Synthetic time series dataset with injected anomalies.
    
    Fields:
        dataset_id: Unique identifier
        signal_config: Signal generation parameters
        anomaly_config: Anomaly injection parameters
        time_series: Generated TimeSeries object
        anomaly_positions: Indices of injected anomalies
        anomaly_types: Types of anomalies (point, contextual, collective)
    """
    dataset_id: str
    signal_config: 'SignalConfig'
    anomaly_config: 'AnomalyConfig'
    time_series: TimeSeries
    anomaly_positions: List[int]
    anomaly_types: List[str]
```

## Schema Specifications

### Dataset Schema (specs/contracts/dataset.schema.yaml)

```yaml
dataset:
  type: object
  required:
    - series_id
    - name
    - source
    - observations_path
    - timestamps_path
  properties:
    series_id:
      type: string
      pattern: "^[A-Z]{2}-[0-9]{3}-[a-z]+$"
    name:
      type: string
      minLength: 1
    source:
      type: string
      enum: ["UCI-Electricity", "UCI-Traffic", "UCI-Synthetic-Control", "Synthetic"]
    observations_path:
      type: string
      pattern: "^data/processed/.*\\.csv$"
    timestamps_path:
      type: string
      pattern: "^data/processed/.*\\.csv$"
    labels_path:
      type: string
      pattern: "^data/processed/.*\\.csv$|^$"
    checksum_sha256:
      type: string
      pattern: "^[a-f0-9]{64}$"
    created_at:
      type: string
      format: date-time
    metadata:
      type: object
```

### Anomaly Score Schema (specs/contracts/anomaly_score.schema.yaml)

```yaml
anomaly_score:
  type: object
  required:
    - timestamp
    - score
    - is_anomaly
    - sequence_id
  properties:
    timestamp:
      type: string
      format: date-time
    score:
      type: number
      minimum: -inf
      maximum: inf
    is_anomaly:
      type: boolean
    uncertainty:
      type: object
      properties:
        variance:
          type: number
        credible_interval_lower:
          type: number
        credible_interval_upper:
          type: number
    component_assignment:
      type: integer
      minimum: 0
    sequence_id:
      type: integer
      minimum: 0
```

### Evaluation Metrics Schema (specs/contracts/evaluation_metrics.schema.yaml)

```yaml
evaluation_metrics:
  type: object
  required:
    - f1_score
    - precision
    - recall
    - auc_roc
    - auc_pr
    - confusion_matrix
    - anomaly_rate
    - runtime_seconds
    - peak_memory_mb
  properties:
    f1_score:
      type: number
      minimum: 0
      maximum: 1
    precision:
      type: number
      minimum: 0
      maximum: 1
    recall:
      type: number
      minimum: 0
      maximum: 1
    auc_roc:
      type: number
      minimum: 0
      maximum: 1
    auc_pr:
      type: number
      minimum: 0
      maximum: 1
    confusion_matrix:
      type: array
      items:
        type: array
        items:
          type: integer
        minItems: 2
        maxItems: 2
      minItems: 2
      maxItems: 2
    anomaly_rate:
      type: number
      minimum: 0
      maximum: 1
    runtime_seconds:
      type: number
      minimum: 0
    peak_memory_mb:
      type: number
      minimum: 0
    threshold_used:
      type: number
    dataset_id:
      type: string
    model_type:
      type: string
      enum: ["DPGMM", "ARIMA", "MovingAverage", "LSTM-AE"]
    evaluated_at:
      type: string
      format: date-time
```

### DPGMM Model Schema (specs/contracts/anomaly_detector.schema.yaml)

```yaml
anomaly_detector:
  type: object
  required:
    - model_type
    - config
    - state
  properties:
    model_type:
      type: string
      const: "DPGMM"
    config:
      type: object
      properties:
        concentration_parameter:
          type: number
          minimum: 0
        n_components_max:
          type: integer
          minimum: 1
        covariance_type:
          type: string
          enum: ["full", "tied", "diag", "spherical"]
        random_seed:
          type: integer
        elbo_tolerance:
          type: number
          minimum: 0
        max_iterations:
          type: integer
          minimum: 1
        streaming_update:
          type: boolean
        concentration_tuning:
          type: boolean
        missing_value_strategy:
          type: string
          enum: ["skip", "impute", "interpolate"]
    state:
      type: object
      properties:
        posterior_weights:
          type: array
          items:
            type: number
        mixture_components:
          type: array
          items:
            type: object
        elbo_history:
          type: array
          items:
            type: number
        n_observations_processed:
          type: integer
          minimum: 0
        concentration_parameter_current:
          type: number
    checkpoint_path:
      type: string
      pattern: "^code/models/checkpoints/.*\\.pkl$"
    created_at:
      type: string
      format: date-time
    updated_at:
      type: string
      format: date-time
```

### Threshold Calibrator Schema (specs/contracts/threshold_calibrator.schema.yaml)

```yaml
threshold_calibrator:
  type: object
  required:
    - calibration_method
    - threshold_value
    - calibration_statistics
  properties:
    calibration_method:
      type: string
      enum: ["percentile", "iqr", "gmm", "adaptive"]
    threshold_value:
      type: number
    calibration_statistics:
      type: object
      properties:
        score_mean:
          type: number
        score_std:
          type: number
        score_min:
          type: number
        score_max:
          type: number
        score_percentile_95:
          type: number
        score_percentile_99:
          type: number
        n_scores:
          type: integer
          minimum: 1
    dataset_id:
      type: string
    calibrated_at:
      type: string
      format: date-time
    expected_anomaly_rate:
      type: number
      minimum: 0
      maximum: 1
    actual_anomaly_rate:
      type: number
      minimum: 0
      maximum: 1
```

## Data Flow

### Processing Pipeline

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Raw Datasets   │────▶│  Download &      │────▶│  Processed      │
│  (UCI/Synthetic)│     │  Validate        │     │  TimeSeries     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                 │
                                                 ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Evaluation     │◀────│  Threshold       │◀────│  DPGMM Model    │
│  Metrics        │     │  Calibration     │     │  (Streaming)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │  Anomaly Scores │
                                        │  + Uncertainty  │
                                        └─────────────────┘
```

### Entity Relationships

```
TimeSeries (1) ──── contains ────▶ (N) StreamingObservation
                                      │
                                      ▼
DPGMMModel (1) ──── processes ────▶ StreamingObservation
                                      │
                                      ▼
DPGMMModel (1) ──── produces ────▶ (N) AnomalyScore
                                      │
                                      ▼
EvaluationMetrics (1) ──── aggregates ────▶ (N) AnomalyScore
```

## Temporal Split Methodology

### Train/Test Split Strategy

All time series datasets are split temporally to prevent data leakage:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Full Time Series                        │
│  ───────────────────────────────────────────────────────────── │
│  [━━━━━━━━━━ TRAIN ━━━━━━━━━━][━━━━━━ TEST ━━━━━━]              │
│  0%                          70%                          100%  │
└─────────────────────────────────────────────────────────────────┘
```

### Dataset-Specific Splits

| Dataset | Start Timestamp | Train End | Test Start | Test End | Train Size | Test Size |
|---------|-----------------|-----------|------------|----------|------------|-----------|
| UCI-Electricity | 2012-07-01 00:00 | 2014-12-31 23:00 | 2015-01-01 00:00 | 2015-06-30 23:00 | ~21,600 | ~4,320 |
| UCI-Traffic | 2015-01-01 00:00 | 2016-06-30 23:00 | 2016-07-01 00:00 | 2016-12-31 23:00 | ~26,280 | ~4,380 |
| Synthetic-Control | 2026-01-01 00:00 | 2026-03-31 23:00 | 2026-04-01 00:00 | 2026-06-30 23:00 | ~21,600 | ~21,600 |

### Temporal Integrity Rules

1. **No Future Leakage**: Training data must never contain timestamps after test start
2. **Continuous Train**: Training period must be contiguous (no gaps)
3. **Continuous Test**: Test period must be contiguous (no gaps)
4. **No Overlap**: Train and test periods must not overlap
5. **Documented Boundaries**: All split timestamps must be recorded in `data-model.md`

### Time Split Implementation

```python
@dataclass
class TimeSplitConfig:
    """
    Configuration for temporal train/test split.
    
    Fields:
        train_start: First timestamp in training set
        train_end: Last timestamp in training set
        test_start: First timestamp in test set
        test_end: Last timestamp in test set
        train_ratio: Fraction of data in training set (0.0-1.0)
    """
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_ratio: float = 0.70
```

## Data Integrity Requirements (Constitution Principle III)

### Checksum Requirements

All data files MUST have SHA256 checksums recorded:

```yaml
# state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
data_checksums:
  data/raw/electricity.csv:
    checksum_sha256: "<64-char-hex>"
    size_bytes: <int>
    downloaded_at: "<ISO8601-timestamp>"
    source_url: "<original-download-url>"
  data/raw/traffic.csv:
    checksum_sha256: "<64-char-hex>"
    size_bytes: <int>
    downloaded_at: "<ISO8601-timestamp>"
    source_url: "<original-download-url>"
  data/processed/synthetic_control.csv:
    checksum_sha256: "<64-char-hex>"
    size_bytes: <int>
    generated_at: "<ISO8601-timestamp>"
    generator_seed: <int>
```

### Validation Rules

1. **Checksum Verification**: Every data access MUST verify checksum matches
2. **Size Validation**: Files must be >1MB (indicates successful download)
3. **Timestamp Recording**: All downloads/generations must be timestamped
4. **Source Tracking**: Original download URLs must be preserved
5. **State File Updates**: Checksums updated via `code/scripts/generate_data_checksums.py`

## File Path Conventions

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── src/
│   │   ├── models/
│   │   │   ├── time_series.py      # TimeSeries, TimeSeriesIterator
│   │   │   ├── dpgmm.py            # DPGMMModel, DPGMMConfig
│   │   │   └── anomaly_score.py    # AnomalyScore
│   │   ├── baselines/
│   │   │   ├── arima.py            # ARIMABaseline
│   │   │   ├── moving_average.py   # MovingAverageBaseline
│   │   │   └── lstm_ae.py          # LSTMAutoencoderBaseline
│   │   ├── evaluation/
│   │   │   ├── metrics.py          # EvaluationMetrics
│   │   │   ├── plots.py            # ROC/PR curve generation
│   │   │   └── statistical_tests.py
│   │   ├── utils/
│   │   │   ├── streaming.py        # StreamingObservation
│   │   │   ├── threshold.py        # ThresholdCalibratorService
│   │   │   ├── memory_profiler.py
│   │   │   └── runtime_monitor.py
│   │   ├── data/
│   │   │   ├── download_datasets.py
│   │   │   └── synthetic_generator.py
│   │   └── services/
│   │       ├── anomaly_detector.py
│   │       └── threshold_calibrator.py
│   ├── tests/
│   │   ├── contract/               # Schema validation tests
│   │   ├── unit/
│   │   └── integration/
│   ├── scripts/
│   │   ├── generate_data_checksums.py
│   │   └── verify_config_compliance.py
│   ├── config.yaml                 # Hyperparameters (<2KB)
│   └── requirements.txt            # Pinned dependencies
├── data/
│   ├── raw/                        # Downloaded datasets
│   │   ├── electricity.csv
│   │   ├── traffic.csv
│   │   └── synthetic_control.csv
│   ├── processed/
│   │   ├── train/                  # Training splits
│   │   ├── test/                   # Test splits
│   │   └── results/                # Evaluation outputs
│   │       ├── metrics/
│   │       ├── plots/
│   │       └── summary.md
│   └── README.md                   # Data provenance documentation
├── specs/
│   ├── 001-bayesian-nonparametrics-anomaly-detection/
│   │   ├── research.md
│   │   ├── data-model.md           # THIS FILE
│   │   ├── quickstart.md
│   │   └── constitution_check.md
│   └── contracts/                  # Schema YAML files
│       ├── dataset.schema.yaml
│       ├── anomaly_score.schema.yaml
│       ├── evaluation_metrics.schema.yaml
│       ├── anomaly_detector.schema.yaml
│       └── threshold_calibrator.schema.yaml
├── state/
│   └── projects/
│       └── PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
├── logs/
│   └── elbo/                       # ELBO convergence logs
└── .github/
    └── workflows/
        └── ci.yml                  # GitHub Actions pipeline
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-01 | Initial specification |

## Related Documents

- `research.md`: Literature review and theoretical foundations
- `quickstart.md`: Usage examples and installation
- `specs/contracts/*.schema.yaml`: Schema definitions for contract tests
- `code/tests/contract/`: Pytest contract validation tests
- `state/projects/PROJ-024-*.yaml`: Artifact checksums and provenance
