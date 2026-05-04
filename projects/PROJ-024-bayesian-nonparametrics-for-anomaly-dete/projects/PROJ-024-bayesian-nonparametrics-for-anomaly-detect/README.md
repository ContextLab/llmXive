# Bayesian Nonparametrics for Anomaly Detection in Time Series

A research project implementing Dirichlet Process Gaussian Mixture Models (DPGMM) with streaming variational inference for time series anomaly detection, alongside classical baselines (ARIMA, Moving Average, LSTM-AE).

## Overview

This project provides:
- **DPGMM Model**: Nonparametric Bayesian model with ADVI variational inference supporting streaming updates
- **Baseline Implementations**: ARIMA, Moving Average, and LSTM-Autoencoder for comparative evaluation
- **Evaluation Pipeline**: Comprehensive metrics (F1, Precision, Recall, AUC) with statistical significance testing
- **Unsupervised Threshold Calibration**: Adaptive anomaly score thresholding without labeled data

## Project Structure

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect/
├── code/
│   ├── src/
│   │   ├── models/          # DPGMM, DPGMMModel, AnomalyScore
│   │   ├── baselines/       # ARIMA, MovingAverage, LSTMAE
│   │   ├── services/        # AnomalyDetectorService, ThresholdCalibratorService
│   │   ├── evaluation/      # Metrics, statistical tests, plots
│   │   ├── data/            # Dataset downloaders, synthetic generators
│   │   └── utils/           # Streaming utilities, checksums
│   ├── tests/
│   │   ├── contract/        # Schema contract tests (9 files)
│   │   ├── unit/            # Unit tests
│   │   └── integration/     # Integration tests
│   ├── scripts/             # Execution scripts
│   └── config.yaml          # Hyperparameters and dataset paths
├── data/
│   ├── raw/                 # Downloaded UCI datasets
│   └── processed/
│       └── results/         # Evaluation outputs (F1 scores, ROC/PR curves)
├── logs/
│   └── elbo/                # ELBO convergence logs
├── state/
│   └── projects/
│       └── PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml
├── specs/
│   └── 001-bayesian-nonparametrics-anomaly-detection/
│       ├── research.md
│       ├── data-model.md
│       └── quickstart.md
└── README.md
```

## Installation

```bash
# Navigate to project directory
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect/code

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pytest --version
```

## Supported Datasets

The project uses three UCI datasets (univariate time series only):

| Dataset | Description | Series Count |
|---------|-------------|--------------|
| Electricity | Hourly electricity demand | 37 series |
| Traffic | Road network traffic flow | Multiple series |
| Synthetic Control Chart | Synthetic time series patterns | 600 series |

See `data/data-dictionary.md` for exact URLs, licenses, and access dates.

## Quick Start

### 1. Download Datasets

```bash
cd code
python scripts/download_datasets.py
```

This will download all three UCI datasets to `data/raw/` with SHA256 checksum validation.

### 2. Run DPGMM Evaluation

```bash
# Run full evaluation pipeline
python scripts/execute_evaluation_pipeline.py

# Or run DPGMM only
python scripts/test_advi_inference.py
```

### 3. Run Baselines

```bash
# ARIMA baseline
python code/src/baselines/arima.py

# Moving Average baseline
python code/src/baselines/moving_average.py

# LSTM-AE baseline
python code/src/baselines/lstm_ae.py
```

## Usage Examples

### DPGMM Model (Streaming Mode)

```python
from models.dp_gmm import DPGMMModel, DPGMMConfig
from utils.streaming import StreamingObservation

# Initialize model with config
config = DPGMMConfig(
    alpha_0=1.0,
    beta_0=1.0,
    kappa_0=1.0,
    nu_0=2,
    max_components=10
)
model = DPGMMModel(config)

# Stream observations
for t, value in enumerate(time_series_data):
    obs = StreamingObservation(timestamp=t, value=value)
    model.update(obs)
    score = model.compute_anomaly_score(obs)
    print(f"t={t}, anomaly_score={score.score}")

# Get model summary
model.print_summary()
```

### ARIMA Baseline

```python
from baselines.arima import ARIMABaseline, ARIMAConfig

config = ARIMAConfig(
    order=(1, 1, 1),
    seasonal_order=(0, 1, 1, 12),
    threshold=2.5
)
baseline = ARIMABaseline(config)
baseline.fit(train_data)

# Get predictions and anomaly scores
predictions = baseline.predict(test_data)
scores = baseline.compute_anomaly_scores(test_data, predictions)
```

### Moving Average Baseline

```python
from baselines.moving_average import MovingAverageBaseline, MovingAverageConfig

config = MovingAverageConfig(
    window_size=20,
    std_threshold=3.0,
    min_samples=100
)
baseline = MovingAverageBaseline(config)
baseline.fit(train_data)

# Get anomaly scores
scores = baseline.compute_anomaly_scores(test_data)
```

### Threshold Calibration (Unsupervised)

```python
from services.threshold_calibrator import ThresholdCalibratorService

calibrator = ThresholdCalibratorService(
    percentile=95.0,
    min_samples=1000,
    adaptive=True
)

# Calibrate threshold on score distribution
threshold = calibrator.calibrate(scores)

# Update threshold adaptively
new_threshold = calibrator.update(scores)
```

## Evaluation Pipeline

### Running Full Evaluation

```bash
python scripts/execute_evaluation_pipeline.py
```

This will:
1. Load all datasets from `data/raw/`
2. Run DPGMM and all baselines on each dataset
3. Compute metrics (F1, Precision, Recall, AUC)
4. Generate ROC/PR curves and confusion matrices
5. Run paired t-tests for statistical significance
6. Save all results to `data/processed/results/`

### Output Artifacts

After evaluation, the following files will exist:

| Path | Description |
|------|-------------|
| `data/processed/results/metrics.json` | All evaluation metrics |
| `data/processed/results/roc_curves/` | ROC curve plots per model |
| `data/processed/results/pr_curves/` | PR curve plots per model |
| `data/processed/results/confusion_matrices/` | Confusion matrix plots |
| `data/processed/results/comparison_summary.json` | Statistical test results |
| `logs/elbo/` | ELBO convergence logs for DPGMM |

## Running Tests

```bash
# All tests
pytest code/tests/

# Contract tests only
pytest code/tests/contract/

# With coverage
pytest --cov=src --cov-report=html code/tests/

# Specific test file
pytest code/tests/integration/test_dpgmm_training.py
```

## Configuration

Hyperparameters are defined in `code/config.yaml`:

```yaml
dpgmm:
  alpha_0: 1.0
  beta_0: 1.0
  kappa_0: 1.0
  nu_0: 2
  max_components: 10
  convergence_threshold: 1e-3
  max_iterations: 1000

threshold:
  percentile: 95.0
  min_samples: 1000

datasets:
  raw_dir: data/raw
  processed_dir: data/processed
```

Derived statistics (dataset sizes, checksums) are stored in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml` to keep `config.yaml` under 2KB.

## License

MIT License - See `LICENSE` file for details.

## References

- DPGMM: Dirichlet Process Gaussian Mixture Models for nonparametric clustering
- ADVI: Automatic Differentiation Variational Inference
- NAB Benchmark: https://github.com/numenta/NAB
- UCI Machine Learning Repository

## Contributing

1. Create a feature branch from `001-bayesian-nonparametrics-anomaly-detection`
2. Implement changes following the task list in `tasks.md`
3. Add tests before implementation (test-driven development)
4. Ensure all contract tests pass
5. Submit pull request for review

## Contact

For questions or issues, refer to the project's `specs/001-bayesian-nonparametrics-anomaly-detection/` documentation.
