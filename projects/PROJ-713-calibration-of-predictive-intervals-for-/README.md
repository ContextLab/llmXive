# Calibration of Predictive Intervals for Time-Series Forecasts

**Project ID**: PROJ-713
**Status**: Active Research Pipeline

This project implements a comprehensive pipeline for evaluating and calibrating predictive intervals for time-series forecasts. It supports multiple models (ARIMA, Prophet, LSTM) and datasets (M4, UCI Electricity), computing empirical coverage, distributional metrics (PIT, CRPS), and statistical significance tests.

## Table of Contents

- [Installation](#installation)
- [Data Fetch Instructions](#data-fetch-instructions)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Output Artifacts](#output-artifacts)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-713-calibration-of-predictive-intervals-for-/
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

 **Key Dependencies**:
 - `statsmodels`: ARIMA modeling
 - `prophet`: Facebook Prophet forecasting
 - `torch`: LSTM implementation
 - `properscoring`: CRPS calculation
 - `scikit-learn`, `scipy`, `pandas`, `numpy`, `matplotlib`: Core data science stack

---

## Data Fetch Instructions

This project requires real external datasets. The pipeline will automatically attempt to fetch them. If automatic fetching fails, manual download is required.

### Supported Datasets

- **M4 Hourly Dataset**: A large collection of time series from the M4 competition.
- **UCI Electricity Dataset**: Hourly electricity consumption data from 370 clients.

### Automatic Fetching

Run the data loader script to fetch and verify data:

```bash
python code/data_loader.py --fetch-all
```

This script:
- Downloads data from verified sources
- Computes checksums for integrity verification
- Stores raw data in `data/raw/`
- **Fails loudly** if URLs are unreachable or checksums do not match (no synthetic fallback).

### Manual Download (if automatic fetch fails)

If the automatic fetch fails, download the datasets manually and place them in `data/raw/`:

1. **M4 Hourly Data**:
 - Source: [M4 Competition Repository](https://github.com/Mcompetitions/M4-methods) or specific verified URL.
 - File: `m4_hourly.csv` (or specific archive).
 - Place in: `data/raw/m4_hourly.csv`

2. **UCI Electricity Data**:
 - Source: [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014).
 - File: `LD2011_2014.txt` (or processed CSV).
 - Place in: `data/raw/uci_electricity.csv`

**Note**: Ensure file names match the expected paths in `code/config.py` or `code/data_loader.py`.

---

## Usage Guide

### Running the Full Pipeline

To run the complete evaluation pipeline (Data Loading -> Model Fitting -> Metrics -> Significance Tests):

```bash
python code/evaluation/runner.py --dataset m4 --models arima prophet lstm
```

**Arguments**:
- `--dataset`: `m4` or `uci`
- `--models`: Space-separated list of models (`arima`, `prophet`, `lstm`)
- `--output-dir`: Custom output directory (default: `results/`)

### Running Specific Modules

**1. Coverage Assessment (User Story 1)**:
```bash
python code/evaluation/runner.py --dataset m4 --models arima --metrics coverage
```
Output: `results/coverage.csv`

**2. Distributional Metrics (User Story 2)**:
```bash
python code/scripts/aggregate_distributional_metrics.py --input results/coverage.csv
```
Output: `results/distributional_metrics.csv`

**3. Significance Testing & Conformal (User Story 3)**:
```bash
python code/evaluation/runner.py --dataset m4 --models arima prophet --significance
```
Output: `results/significance_test.csv`, `results/conformal_results.csv`

### Benchmarking

To measure runtime on a subset:
```bash
python code/scripts/benchmark_pipeline.py --dataset m4 --subset 10
```
Output: `results/benchmark_timing.csv`

---

## Project Structure

```text
projects/PROJ-713-calibration-of-predictive-intervals-for-/
├── code/
│ ├── config.py # Hyperparameters, paths, seeds
│ ├── data_loader.py # Data fetching, splitting, standardization
│ ├── utils/
│ │ ├── logger.py # Structured logging
│ │ └── exceptions.py # Custom errors
│ ├── models/
│ │ ├── arima_model.py # Statsmodels wrapper
│ │ ├── prophet_model.py # Prophet wrapper
│ │ └── lstm_model.py # PyTorch implementation
│ ├── metrics/
│ │ ├── coverage.py # Empirical coverage calculation
│ │ ├── pit.py # Probability Integral Transform
│ │ └── crps.py # Continuous Ranked Probability Score
│ ├── calibration/
│ │ └── conformal.py # Self-Calibrating Conformal Wrapper
│ ├── evaluation/
│ │ ├── runner.py # Main pipeline orchestrator
│ │ └── bootstrap_test.py # Paired bootstrap significance tests
│ └── scripts/
│ ├── aggregate_distributional_metrics.py
│ ├── benchmark_pipeline.py
│ └── export_results.py
├── data/
│ ├── raw/ # Downloaded raw datasets
│ └── processed/ # Preprocessed splits
├── results/
│ ├── coverage.csv
│ ├── distributional_metrics.csv
│ ├── significance_test.csv
│ └── conformal_results.csv
├── tests/
│ ├── unit/
│ ├── contract/
│ └── integration/
├── requirements.txt
└── README.md
```

---

## Configuration

Edit `code/config.py` to modify:
- **Paths**: `PROJECT_ROOT`, `DATA_DIR`, `RESULTS_DIR`
- **Hyperparameters**:
 - `TRAIN_SPLIT`: 0.8 (80% training)
 - `CONF_LEVELS`: `[0.80, 0.95]`
 - `RANDOM_SEED`: 42
- **Model Parameters**:
 - ARIMA order, Prophet uncertainty samples, LSTM hidden units/epochs

---

## Output Artifacts

The pipeline generates the following CSV files in `results/`:

| File | Description |
|------|-------------|
| `coverage.csv` | Empirical coverage rates vs. nominal levels for each model/series |
| `distributional_metrics.csv` | PIT histograms, Ljung-Box p-values, CRPS scores |
| `significance_test.csv` | Paired bootstrap p-values for model comparisons |
| `conformal_results.csv` | Baseline vs. Conformal coverage comparison |
| `benchmark_timing.csv` | Runtime measurements for pipeline stages |

---

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

**Test Categories**:
- **Unit Tests**: Individual function logic (e.g., `test_coverage.py`)
- **Contract Tests**: Schema validation (e.g., `test_data_schema.py`)
- **Integration Tests**: End-to-end pipeline validation (e.g., `test_coverage_arima.py`)

**Specific Test Commands**:
```bash
# Test data loader split logic
pytest tests/unit/test_data_loader.py -v

# Test ARIMA coverage calculation
pytest tests/integration/test_coverage_arima.py -v

# Test PIT uniformity
pytest tests/integration/test_pit_ljung_box_test.py -v
```

---

## Troubleshooting

### Data Fetch Failures
- **Error**: `ValueError: Data fetch failed. Checksum mismatch or URL unreachable.`
- **Fix**: Verify internet connection, check `data/raw/` for partial downloads, or download manually as described in [Data Fetch Instructions](#data-fetch-instructions).

### Model Convergence Errors
- **Error**: `ModelConvergenceError: ARIMA failed to converge for series X.`
- **Fix**: The pipeline logs these errors and continues. Check `logs/` for details. Consider adjusting model parameters in `config.py`.

### CUDA/OOM Errors (LSTM)
- **Error**: `RuntimeError: CUDA out of memory`
- **Fix**: The LSTM model is configured for CPU-only training by default. If CUDA is enabled accidentally, set `CUDA_VISIBLE_DEVICES=""` or check `code/models/lstm_model.py` for device settings.

### Missing Output Files
- **Error**: `FileNotFoundError: results/coverage.csv not found`
- **Fix**: Ensure the full pipeline (`runner.py`) was executed successfully. Check for early exits in logs.

---

## License

Research project for academic purposes.

## Contact

For issues, open a GitHub issue in the project repository.