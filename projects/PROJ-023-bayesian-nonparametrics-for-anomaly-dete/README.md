# Bayesian Nonparametrics for Anomaly Detection in Time Series

**Project ID**: PROJ-023
**Status**: Research Pipeline Implementation
**Version**: 1.0.0

## Overview

This project implements a research pipeline for detecting anomalies in time series data using Bayesian Nonparametrics (specifically Sparse Variational Inference Gaussian Processes) and compares them against classical statistical baselines (Shewhart, CUSUM) and deep learning baselines (VAE).

The pipeline is designed to run on CPU-only resources with strict memory (7GB) and time (6h) constraints. All data is sourced from real public repositories (UCR/UCI) with synthetic anomalies injected under controlled, reproducible parameters.

## Project Structure

The repository follows a strict directory structure to separate code, data, results, and documentation:

```text
.
├── README.md # This file
├── requirements.txt # Core dependencies (pymc, numpyro, pandas, etc.)
├── requirements-dev.txt # Test and linting dependencies
├── code/ # Source code
│ ├── lib/ # Shared libraries
│ │ ├── anomaly_injector.py
│ │ ├── data_loader.py
│ │ ├── metrics.py
│ │ └── utils.py
│ ├── scripts/ # Executable pipeline scripts
│ │ ├── download_data.py
│ │ ├── inject_anomalies.py
│ │ ├── bayesian_gp.py
│ │ ├── baseline_shewhart.py
│ │ ├── baseline_cusum.py
│ │ ├── baseline_vae.py
│ │ ├── evaluate.py
│ │ ├── sensitivity_analysis.py
│ │ ├── render_fig1.py
│ │ ├── render_fig2.py
│ │ └── verify_paths.py
│ ├── tests/ # Unit and integration tests
│ │ ├── contract/
│ │ ├── integration/
│ │ ├── test_anomaly_injector.py
│ │ ├── test_data_injection.py
│ │ ├── test_metrics.py
│ │ └── test_utils.py
│ └── setup_linting.py
├── data/ # Data artifacts
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Preprocessed data with injected anomalies
│ ├── results/ # Model predictions and evaluation metrics
│ ├── PROVENANCE.md # Data source metadata and checksums
│ └── VERSION.txt
├── paper/ # Research outputs
│ ├── figures/ # Generated plots (fig1, fig2)
│ ├── results.md # Summary of findings and statistical tests
│ └── README.md
└── contracts/ # JSON/YAML schemas for data and results
 ├── dataset.schema.yaml
 ├── evaluation.schema.yaml
 └── prediction.schema.yaml
```

## Prerequisites

- Python 3.11+
- CPU-only execution environment (Max 7GB RAM)
- pip package manager

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install -r requirements-dev.txt
 ```

## Usage

The pipeline is executed sequentially. Ensure you have sufficient disk space and memory.

### 1. Data Download & Preparation
Downloads real time series data and verifies checksums.
```bash
python code/scripts/download_data.py
```

### 2. Anomaly Injection
Injects synthetic anomalies (mean shift, variance spike, drift) into the data.
```bash
python code/scripts/inject_anomalies.py
```

### 3. Bayesian Inference (Core)
Runs Sparse Variational Inference Gaussian Process for anomaly scoring.
```bash
python code/scripts/bayesian_gp.py
```

### 4. Baseline Execution
Runs statistical and deep learning baselines for comparison.
```bash
python code/scripts/baseline_shewhart.py
python code/scripts/baseline_cusum.py
python code/scripts/baseline_vae.py
```

### 5. Evaluation & Statistical Analysis
Computes metrics (F1, AUC, Bootstrap CI) and performs statistical significance testing.
```bash
python code/scripts/evaluate.py
python code/scripts/sensitivity_analysis.py
```

### 6. Visualization
Generates research figures.
```bash
python code/scripts/render_fig1.py
python code/scripts/render_fig2.py
```

## Data Provenance

All data sources are documented in `data/PROVENANCE.md`. This file includes:
- Source URLs (UCR Archive, NAB)
- Dataset versions and SHA-256 checksums
- License information
- Injection parameters used for ground truth generation

**Note**: The pipeline does not use synthetic data for evaluation; it uses real time series with known, injected anomalies to ensure ground truth validity.

## Methodology

- **Bayesian Approach**: Sparse Variational Inference (SVI) Gaussian Processes using PyMC/Numpyro.
- **Baselines**: Shewhart charts, CUSUM, and Variational Autoencoders (VAE).
- **Metrics**: Precision, Recall, F1-Score, AUC-ROC, Brier Score.
- **Statistical Testing**: Wilcoxon signed-rank test and Bootstrap Confidence Intervals with Bonferroni correction.
- **Constraints**: CPU-only, <7GB RAM, <6h runtime.

## Reproducibility

- **Seed Pinning**: All random seeds are fixed via `code/lib/utils.py`.
- **Version Control**: Dependencies are pinned in `requirements.txt`.
- **Schema Enforcement**: All data and results conform to schemas in `contracts/`.
- **Memory Profiling**: Scripts include `tracemalloc` wrappers to enforce the 7GB limit.

## License

This research code is provided for academic and research purposes. See `LICENSE` for details.

## Contact

For issues or contributions, please open an issue in the repository.