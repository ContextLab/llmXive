# Bayesian Nonparametrics for Anomaly Detection in Time Series

This project implements a Dirichlet Process Gaussian Mixture Model (DPGMM) for streaming anomaly detection in time series data, along with baseline comparison models (ARIMA, Moving Average with Z-Score, and LSTM Autoencoder).

## Quick Start

### Installation

```bash
cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### Download Datasets

```bash
python -m scripts.download_datasets
```

This downloads UCI datasets (Electricity, Traffic, Synthetic Control Chart) to `data/raw/` and validates checksums.

### Run DPGMM Model

```bash
python -m models.dp_gmm
```

This processes the time series data using the DPGMM model and outputs anomaly scores to `data/processed/results/`.

### Run Baseline Comparisons

#### ARIMA Baseline

```bash
python -m baselines.arima
```

#### Moving Average with Z-Score Baseline

```bash
python -m baselines.moving_average
```

#### LSTM Autoencoder Baseline

```bash
python -m baselines.lstm_ae
```

## Project Structure

```
code/
├── baselines/
│   ├── arima.py              # ARIMA baseline implementation
│   ├── moving_average.py     # Moving Average with Z-Score baseline
│   └── lstm_ae.py            # LSTM Autoencoder baseline
├── data/
│   ├── synthetic_generator.py # Synthetic dataset generation
│   └── download_datasets.py   # Dataset download utilities
├── evaluation/
│   ├── metrics.py            # F1-score, precision, recall, AUC computation
│   ├── plots.py              # ROC/PR curve generation
│   └── statistical_tests.py  # Paired t-tests with Bonferroni correction
├── models/
│   ├── anomaly_score.py      # AnomalyScore dataclass
│   ├── dp_gmm.py             # DPGMMModel with stick-breaking construction
│   └── time_series.py        # TimeSeries dataclass
├── scripts/
│   ├── benchmark_dp_gmm_performance.py  # Performance benchmarking
│   ├── compare_performance.py           # Model comparison utilities
│   ├── generate_data_checksums.py       # Checksum generation for data files
│   ├── verify_config_compliance.py      # Config validation
│   └── ... (other utility scripts)
├── utils/
│   ├── streaming.py          # Streaming observation processing
│   ├── memory_profiler.py    # Memory usage profiling
│   ├── threshold.py          # Threshold calibration utilities
│   └── time_split.py         # Time-ordered train/test split
├── config.yaml               # Hyperparameters and dataset paths
└── requirements.txt          # Pinned dependencies
```

## Usage Examples

### Processing a Time Series with DPGMM

```python
from models.dp_gmm import DPGMMModel, DPGMMConfig
from models.time_series import TimeSeries
import numpy as np

# Initialize model with configuration
config = DPGMMConfig(
    concentration_prior=1.0,
    max_components=10,
    convergence_threshold=0.001,
    max_iterations=500
)
model = DPGMMModel(config)

# Process streaming observations
observations = np.random.randn(1000, 1)  # Replace with actual data
for obs in observations:
    score = model.process_observation(obs)
    if score.is_anomaly:
        print(f"Anomaly detected at index {model.observation_count}")
```

### Computing Anomaly Scores

```python
from models.dp_gmm import DPGMMModel
import numpy as np

model = DPGMMModel()
data = np.loadtxt('data/raw/electricity.csv')

# Batch scoring
scores = model.compute_anomaly_scores_batch(data)
print(f"Detected {sum(s.is_anomaly for s in scores)} anomalies")
```

### Running Baseline Comparison

```python
from baselines.arima import ARIMABaseline
from baselines.moving_average import MovingAverageBaseline
from baselines.lstm_ae import LSTMAE
from models.dp_gmm import DPGMMModel
from evaluation.metrics import compute_all_metrics

# Load data
data = np.loadtxt('data/raw/traffic.csv')
ground_truth = np.loadtxt('data/raw/traffic_labels.csv')

# Run all models
dpgmm_scores = DPGMMModel().compute_anomaly_scores_batch(data)
arima_scores = ARIMABaseline().compute_scores(data)
ma_scores = MovingAverageBaseline().compute_scores(data)
lstm_scores = LSTMAE().compute_scores(data)

# Compare performance
metrics = compute_all_metrics(
    ground_truth=ground_truth,
    dpgmm_scores=dpgmm_scores,
    arima_scores=arima_scores,
    ma_scores=ma_scores,
    lstm_scores=lstm_scores
)
```

### Threshold Calibration (Unlabeled Data)

```python
from utils.threshold import ThresholdCalibratorService
from models.dp_gmm import DPGMMModel

model = DPGMMModel()
calibrator = ThresholdCalibratorService()

# Score unlabeled data
data = np.loadtxt('data/raw/electricity.csv')
scores = model.compute_anomaly_scores_batch(data)

# Calibrate threshold using 95th percentile
threshold = calibrator.calibrate(scores, percentile=95)
print(f"Calibrated threshold: {threshold}")
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# Hyperparameters
dpgmm:
  concentration_prior: 1.0
  max_components: 10
  convergence_threshold: 0.001
  max_iterations: 500

# Dataset paths
datasets:
  electricity: data/raw/electricity.csv
  traffic: data/raw/traffic.csv
  synthetic_control: data/raw/synthetic_control.csv

# Random seeds for reproducibility
random_seed: 42
```

## Testing

```bash
# Run all tests
pytest tests/ -v --cov=src --cov-report=html

# Run contract tests
pytest tests/contract/ -v

# Run integration tests
pytest tests/integration/ -v

# Check test coverage
coverage report -m
```

## Performance Benchmarks

```bash
# Benchmark DPGMM performance
python -m scripts.benchmark_dp_gmm_performance

# Compare all models
python -m scripts.compare_performance
```

## Output Artifacts

After running the full pipeline, results are saved to `data/processed/results/`:

- `anomaly_scores.json` - Scores for all models
- `evaluation_metrics.json` - F1, precision, recall, AUC
- `roc_curves.png` - ROC curve visualization
- `pr_curves.png` - Precision-Recall curve visualization
- `comparison_summary.json` - Statistical test results

## License

MIT License - see LICENSE file for details.

## References

- NAB Benchmark: https://github.com/numenta/NAB
- UCI Machine Learning Repository: https://archive.ics.uci.edu/
- DPGMM: Blei, D. M., & Jordan, M. I. (2006). Variational inference for Dirichlet process mixtures.
execute: false