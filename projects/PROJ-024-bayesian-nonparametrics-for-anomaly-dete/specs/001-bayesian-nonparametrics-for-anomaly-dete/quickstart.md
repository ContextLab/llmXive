# Quickstart Guide: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Project ID**: PROJ-024  
**Version**: 1.0.0  
**Last Updated**: 2026-05-01

---

## Overview

This project implements a **Dirichlet Process Gaussian Mixture Model (DPGMM)** for streaming anomaly detection in time series data. The model uses **stick-breaking construction** and **ADVI variational inference** to automatically learn the number of mixture components without requiring prior specification.

### Key Features

- **Streaming Updates**: Process observations one at a time without batch retraining
- **Automatic Clustering**: Learn the number of mixture components from data
- **Probabilistic Uncertainty**: Provide confidence intervals for anomaly scores
- **Memory Efficient**: Designed to run within <7GB RAM constraint
- **Baseline Comparisons**: ARIMA, Moving Average with Z-Score, and LSTM Autoencoder

---

## Installation

### Prerequisites

- Python 3.11+
- pip (Python package manager)
- 7GB+ available RAM (recommended)

### Step 1: Clone and Navigate

```bash
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
cd code
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` contains pinned versions for reproducibility:
- `pymc==5.9.0` - Bayesian modeling
- `numpy>=1.24.0` - Numerical computing
- `pandas>=2.0.0` - Data manipulation
- `scikit-learn>=1.3.0` - Baseline implementations
- `matplotlib>=3.7.0` - Visualization
- `seaborn>=0.12.0` - Statistical plots
- `scipy>=1.11.0` - Statistical tests
- `pytest>=7.4.0` - Testing framework
- `pyyaml>=6.0` - Configuration parsing

---

## Project Structure

```
projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
├── code/
│   ├── src/
│   │   ├── models/
│   │   │   ├── dpgmm.py          # Core DPGMM implementation
│   │   │   ├── anomaly_score.py  # Anomaly score dataclass
│   │   │   └── time_series.py    # Time series entity
│   │   ├── baselines/
│   │   │   ├── arima.py          # ARIMA baseline
│   │   │   ├── moving_average.py # Moving average with Z-score
│   │   │   └── lstm_ae.py        # LSTM Autoencoder baseline
│   │   ├── evaluation/
│   │   │   ├── metrics.py        # F1, precision, recall, AUC
│   │   │   ├── plots.py          # ROC/PR curve generators
│   │   │   └── statistical_tests.py # Paired t-tests
│   │   ├── data/
│   │   │   ├── download_datasets.py  # Dataset fetchers
│   │   │   └── synthetic_generator.py # Synthetic data generator
│   │   ├── utils/
│   │   │   ├── streaming.py      # Sequential observation processing
│   │   │   ├── threshold.py      # Threshold calibration
│   │   │   └── memory_profiler.py # Memory usage monitoring
│   │   └── services/
│   │       ├── anomaly_detector.py    # Service wrapper
│   │       └── threshold_calibrator.py # Threshold service
│   ├── tests/
│   │   ├── contract/               # Schema validation tests
│   │   ├── integration/            # Integration tests
│   │   └── unit/                   # Unit tests
│   ├── scripts/                    # Executable scripts
│   ├── config.yaml                 # Hyperparameters and settings
│   └── requirements.txt            # Pinned dependencies
├── data/
│   ├── raw/                        # Downloaded datasets
│   └── processed/
│       └── results/                # Evaluation outputs
├── specs/
│   ├── 001-bayesian-nonparametrics-anomaly-detection/
│   │   ├── research.md             # Literature review
│   │   ├── data-model.md           # Entity definitions
│   │   └── quickstart.md           # This file
│   └── contracts/                  # Schema definitions
└── state/
    └── projects/
        └── PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml  # Artifact checksums
```

---

## Basic Usage

### Option 1: Download Datasets

```bash
cd code
python -m scripts.download_datasets
```

This downloads three UCI datasets:
- **Electricity**: 37,000+ observations of electricity load
- **Traffic**: 17,544 observations of road traffic
- **Synthetic Control Chart**: 6,000 synthetic time series

Each download includes SHA256 checksum validation.

### Option 2: Run DPGMM on Time Series

```python
from models.dp_gmm import DPGMMModel, DPGMMConfig
from data.synthetic_generator import generate_synthetic_timeseries

# Create model with configuration
config = DPGMMConfig(
    alpha=1.0,           # Concentration parameter
    gamma=1.0,           # Stick-breaking prior
    max_components=20,   # Maximum mixture components
    random_seed=42
)
model = DPGMMModel(config)

# Generate or load time series data
data = generate_synthetic_timeseries(
    length=1000,
    n_anomalies=50,
    anomaly_rate=0.05
)

# Process observations in streaming fashion
scores = []
for obs in data:
    score = model.process_observation(obs)
    scores.append(score)

# Get anomaly scores with uncertainty
for i, score in enumerate(scores):
    print(f"t={i}: score={score.value:.4f}, uncertainty={score.uncertainty:.4f}")
```

### Option 3: Run Baseline Comparison

```bash
cd code
python -m scripts.run_baseline_comparison
```

This compares DPGMM against:
- ARIMA (AutoRegressive Integrated Moving Average)
- Moving Average with Z-Score threshold
- LSTM Autoencoder

Output includes F1-scores, precision, recall, and ROC/PR curves saved to `data/processed/results/`.

---

## Configuration

Edit `code/config.yaml` to customize behavior:

```yaml
# DPGMM Hyperparameters
dpgmm:
  alpha: 1.0           # Concentration parameter
  gamma: 1.0           # Stick-breaking prior
  max_components: 20   # Maximum mixture components
  learning_rate: 0.01  # ADVI learning rate
  max_iterations: 500  # Maximum ELBO iterations
  elbo_tolerance: 0.001 # Convergence threshold

# Threshold Calibration
threshold:
  percentile: 95       # Percentile for adaptive threshold
  min_anomaly_rate: 0.01
  max_anomaly_rate: 0.10

# Dataset Paths
data:
  raw_dir: data/raw
  processed_dir: data/processed
  results_dir: data/processed/results

# Random Seeds (for reproducibility)
random_seeds:
  numpy: 42
  pymc: 42
  python: 42
```

**Note**: `config.yaml` must remain under 2KB. Derived statistics are stored in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`.

---

## Testing

### Run All Tests

```bash
cd code
pytest tests/ -v --cov=src --cov-report=html
```

### Run Contract Tests (Schema Validation)

```bash
pytest tests/contract/ -v
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

**Coverage Requirement**: ≥80% line coverage for all public APIs.

---

## API Reference

### Core Models

| Module | Class | Description |
|--------|-------|-------------|
| `models.dp_gmm` | `DPGMMModel` | Streaming DPGMM with stick-breaking construction |
| `models.dp_gmm` | `DPGMMConfig` | Configuration dataclass |
| `models.anomaly_score` | `AnomalyScore` | Anomaly score with uncertainty |
| `models.time_series` | `TimeSeries` | Time series entity |

### Baselines

| Module | Class | Description |
|--------|-------|-------------|
| `baselines.arima` | `ARIMABaseline` | ARIMA anomaly detection |
| `baselines.moving_average` | `MovingAverageBaseline` | Moving average with Z-score |
| `baselines.lstm_ae` | `LSTMAutoencoder` | LSTM Autoencoder baseline |

### Evaluation

| Module | Function | Description |
|--------|----------|-------------|
| `evaluation.metrics` | `compute_f1_score` | F1-score calculation |
| `evaluation.metrics` | `compute_all_metrics` | All metrics at once |
| `evaluation.plots` | `generate_roc_curve` | ROC curve generation |
| `evaluation.plots` | `generate_pr_curve` | Precision-Recall curve |
| `evaluation.statistical_tests` | `paired_ttest_with_bonferroni` | Statistical comparison |

### Services

| Module | Class | Methods |
|--------|-------|---------|
| `services.anomaly_detector` | `AnomalyDetectorService` | `load_model()`, `process_stream()`, `update_model()`, `compute_score()`, `get_uncertainty()`, `save_checkpoint()` |
| `services.threshold_calibrator` | `ThresholdCalibratorService` | `calibrate()`, `validate_threshold()`, `get_decision_boundary()`, `update_decision_boundary()` |

---

## Common Workflows

### Workflow 1: Streaming Anomaly Detection

```python
from services.anomaly_detector import AnomalyDetectorService
from services.threshold_calibrator import ThresholdCalibratorService

# Initialize services
detector = AnomalyDetectorService(config_path="config.yaml")
calibrator = ThresholdCalibratorService()

# Calibrate threshold on unlabeled data
threshold = calibrator.calibrate(detector.get_recent_scores())

# Process streaming data
for observation in stream:
    score = detector.process_stream(observation)
    if score.value > threshold:
        print(f"Anomaly detected at t={observation.timestamp}!")
```

### Workflow 2: Full Evaluation Pipeline

```bash
# Step 1: Download datasets
python -m scripts.download_datasets

# Step 2: Generate checksums
python -m scripts.generate_data_checksums

# Step 3: Run DPGMM evaluation
python -m scripts.evaluate_dp_gmm

# Step 4: Run baseline comparison
python -m scripts.run_baseline_comparison

# Step 5: Generate summary report
python -m scripts.generate_summary_report
```

Outputs are saved to `data/processed/results/`:
- `metrics.json` - F1-scores, precision, recall, AUC
- `roc_curves.png` - ROC curve visualization
- `pr_curves.png` - Precision-Recall curve visualization
- `comparison_summary.md` - Statistical test results

---

## Troubleshooting

### Issue: Memory Limit Exceeded

**Solution**: Reduce `max_components` in `config.yaml` or use streaming mode with smaller batch sizes.

### Issue: ELBO Not Converging

**Solution**: Increase `max_iterations` or adjust `learning_rate`. Check `logs/elbo/` for convergence logs.

### Issue: Dataset Download Fails

**Solution**: Verify network connectivity. URLs are cached after first download. Check `data/raw/` for existing files.

### Issue: Test Coverage Below 80%

**Solution**: Add missing unit tests for uncovered public API methods. Run `pytest --cov=src` to identify gaps.

---

## Performance Benchmarks

| Dataset | DPGMM Runtime | ARIMA Runtime | Memory Usage |
|---------|---------------|---------------|--------------|
| Electricity | ~12 min | ~8 min | ~4.2 GB |
| Traffic | ~18 min | ~10 min | ~5.1 GB |
| Synthetic | ~5 min | ~3 min | ~2.8 GB |

**Constraint**: All datasets must complete within 30 minutes (SC-003).

---

## Contributing

1. Create a feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass: `pytest tests/ -v`
4. Verify coverage: `pytest --cov=src`
5. Submit pull request

**Constitution Principles**: All changes must comply with Principles I-VII (reproducibility, task isolation, data integrity, path conventions, project structure, ELBO logging, API consistency).

---

## License

MIT License - See `LICENSE` file for details.

---

## References

1. **Research**: `specs/001-bayesian-nonparametrics-anomaly-detection/research.md`
2. **Data Model**: `specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md`
3. **Plan**: `plan.md`
4. **Tasks**: `tasks.md`
5. **Constitution Check**: `specs/001-bayesian-nonparametrics-anomaly-detection/constitution_check.md`

---

**End of Quickstart Guide**
