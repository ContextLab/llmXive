# Calibration of Predictive Intervals for Time-Series Forecasts

**Project ID:** PROJ-713
**Status:** Active Research Pipeline

This project implements a comprehensive pipeline for evaluating and calibrating predictive intervals for time-series forecasting models. It supports ARIMA, Prophet, and LSTM models, with rigorous statistical testing for coverage, distributional calibration (PIT, CRPS), and conformal prediction adjustments.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Data Preparation](#data-preparation)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Output Artifacts](#output-artifacts)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🚀 Features

- **Multi-Model Support**: ARIMA (Statsmodels), Prophet, and LSTM (PyTorch).
- **Empirical Coverage**: Calculates empirical coverage rates for nominal intervals (0.80, 0.95).
- **Distributional Calibration**: Probability Integral Transform (PIT) histograms and Ljung-Box tests for uniformity.
- **Continuous Ranked Probability Score (CRPS)**: Probabilistic forecast accuracy metric.
- **Statistical Significance**: Paired bootstrap tests for comparing model performance.
- **Conformal Prediction**: Self-Calibrating Conformal Prediction wrapper for improved coverage.
- **Robust Data Handling**: Streaming support for large datasets (UCI Electricity) with strict checksum verification.

## 🛠 Prerequisites

- **Python**: 3.11 or higher
- **Package Manager**: `pip` (or `conda`)
- **System Dependencies**:
 - `gcc` / `build-essential` (required for compiling some Python packages)
 - `git` (for fetching submodules if applicable)

## 📦 Installation

1. **Clone the repository** (if applicable) or navigate to the project root:
 ```bash
 cd projects/PROJ-713-calibration-of-predictive-intervals-for-
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

 *Note: `requirements.txt` includes `statsmodels`, `prophet`, `torch`, `properscoring`, `scikit-learn`, `scipy`, `pandas`, `numpy`, and `matplotlib`.*

4. **Verify installation**:
 ```bash
 python -c "import statsmodels; import prophet; import torch; print('All core dependencies loaded successfully.')"
 ```

## 📂 Project Structure

```text
.
├── code/
│ ├── config.py # Hyperparameters and path constants
│ ├── data_loader.py # Data fetching and preprocessing
│ ├── models/ # Model implementations (ARIMA, Prophet, LSTM)
│ ├── metrics/ # Coverage, PIT, CRPS calculations
│ ├── evaluation/ # Pipeline runner and bootstrap tests
│ ├── calibration/ # Conformal prediction wrapper
│ ├── utils/ # Logging and exception handling
│ └── scripts/ # Utility scripts (export results, setup)
├── data/
│ ├── raw/ # Downloaded raw datasets (M4, UCI)
│ └── processed/ # Preprocessed/standardized data
├── results/ # Output CSVs and figures
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## 📥 Data Preparation

The pipeline supports **M4** (Hourly subset) and **UCI Electricity** datasets. Data is automatically fetched and verified upon first run, or can be prepared manually.

### Automatic Fetching (Recommended)

Run the main evaluation script; it will attempt to download and verify data:
```bash
python code/evaluation/runner.py --dataset m4_hourly
```

### Manual Preparation

If you prefer to download data manually:

1. **M4 Dataset**:
 - Download the M4 Hourly data from the official repository.
 - Place the CSV files in `data/raw/m4/`.

2. **UCI Electricity**:
 - Download the "Electricity Load Diagrams" dataset from the UCI Machine Learning Repository.
 - Place the CSV file in `data/raw/uci/`.

**Verification**:
The `data_loader.py` module enforces checksum verification. If the downloaded files do not match the expected checksums, the process will fail loudly with a `ValueError`.

## 🏃 Usage Guide

### 1. Setup Project Directories

Ensure all required directories exist:
```bash
python code/setup_project_structure.py
python code/setup_results_dirs.py
```

### 2. Run the Full Evaluation Pipeline

Execute the main runner to process all series, fit models, and compute metrics:

```bash
python code/evaluation/runner.py \
 --dataset m4_hourly \
 --models arima prophet lstm \
 --coverage-levels 0.80 0.95 \
 --output-dir results/
```

**Arguments**:
- `--dataset`: Name of the dataset to load (`m4_hourly`, `uci_electricity`).
- `--models`: List of models to run (default: `arima`, `prophet`, `lstm`).
- `--coverage-levels`: Nominal coverage levels to test (default: `0.80`, `0.95`).
- `--output-dir`: Directory for results (default: `results/`).

### 3. Conformal Calibration

After standard evaluation, run the conformal wrapper to improve coverage:

```bash
python code/calibration/conformal.py \
 --input results/coverage.csv \
 --output results/conformal_results.csv
```

### 4. Significance Testing

Compare models using paired bootstrap tests:

```bash
python code/evaluation/bootstrap_test.py \
 --results results/coverage.csv \
 --output results/significance_test.csv
```

### 5. Export Results

Aggregate and export all results to a single report:

```bash
python code/scripts/export_results.py
```

## ⚙️ Configuration

Edit `code/config.py` to modify:
- **Random Seeds**: For reproducibility.
- **Data Paths**: Default directories for raw/processed data.
- **Model Hyperparameters**:
 - ARIMA: Order, seasonal periods.
 - Prophet: Seasonality modes, uncertainty samples.
 - LSTM: Hidden units, epochs, learning rate.
- **Bootstrap Parameters**: Number of resamples, significance level.

## 📊 Output Artifacts

The pipeline generates the following files in the `results/` directory:

| File | Description |
|------|-------------|
| `coverage.csv` | Empirical coverage rates vs. nominal levels for each model/series. |
| `distributional_metrics.csv` | PIT histograms, Ljung-Box p-values, and CRPS scores. |
| `significance_test.csv` | Bootstrap p-values for pairwise model comparisons. |
| `conformal_results.csv` | Coverage improvements after conformal wrapping. |
| `figures/` | PIT histograms and coverage deviation plots. |

## 🧪 Testing

Run the test suite to verify implementation correctness:

```bash
python -m pytest tests/ -v
```

**Key Test Modules**:
- `tests/unit/test_data_loader.py`: Verifies 80/20 split and streaming.
- `tests/integration/test_coverage_arima.py`: End-to-end ARIMA coverage.
- `tests/integration/test_pit_ljung_box_test.py`: PIT uniformity logic.

## 🐛 Troubleshooting

- **Data Fetch Failures**:
 - Ensure internet connectivity.
 - Verify that the `data_loader.py` checksums match the source files.
 - If a URL is unreachable, the script will raise a `ValueError` (no silent fallback).

- **Model Convergence Errors**:
 - ARIMA: Some series may be non-stationary. Check logs for `ModelConvergenceError`.
 - LSTM: If NaN/Inf intervals occur, the model automatically retries with a reduced learning rate (per spec).

- **Memory Issues (UCI)**:
 - The `data_loader` uses streaming/chunked loading for UCI data. Ensure you have at least 7GB of RAM available for processing.

- **Import Errors**:
 - Ensure `requirements.txt` is fully installed.
 - Verify Python version is 3.11+.

## 📄 License

This project is part of the llmXive automated science pipeline.