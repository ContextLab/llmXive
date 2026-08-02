# llmXive: Extending Kairos - A Native World Model Stack for Physical AI

**Project ID**: PROJ-888-llmxive-follow-up-extending-kairos-a-nat

## Overview

This project implements a discrete scaling study of the **Kairos** world model stack, focusing on the transition from continuous visual modalities to discrete state vectors for Physical AI. The goal is to quantify the stability and information density thresholds required for robust world modeling under resource constraints (CPU-only, limited RAM).

The pipeline converts the **LIBERO** dataset into discrete, JSON-serialized state vectors with configurable quantization (4/8/16-bit) and noise injection, trains a CPU-only adapter model, and performs statistical stability analysis to identify minimum information density thresholds.

## Key Features

- **Data Construction**: Automated download, quantization, and noise injection for the LIBERO dataset.
- **CPU-Only Training**: Optimized training loop for environments without GPU acceleration.
- **Stability Analysis**: Statistical validation (paired t-test/Wilcoxon) to measure relative degradation against continuous baselines.
- **Resource Awareness**: Built-in monitoring for RAM usage, CPU load, and graceful exit strategies for long-running jobs.

## Prerequisites

- Python 3.9+
- pip
- 7GB+ available RAM (for dataset processing)
- 20GB+ disk space

## Quickstart

### 1. Setup Environment

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Directory Structure

The project initializes the following directories automatically or via manual creation:
- `code/`: Source code modules
- `tests/`: Unit and integration tests
- `data/`: Raw and processed datasets
- `state/`: Checkpoint and state files
- `docs/`: Documentation and reports

### 3. Run the Data Pipeline (User Story 1)

This step downloads a subset of the LIBERO dataset, quantizes it, injects noise, and saves the result.

```bash
cd code
python main.py --mode download --quantize --noise --subset-size 50
```

**Expected Output**:
- `data/processed/test_subset.json`: Discrete state vectors
- Logs confirming successful download and processing.

### 4. Run CPU-Only Training (User Story 2)

Trains the Kairos adapter on the processed discrete data.

```bash
cd code
python main.py --mode train --epochs 10 --batch-size 32
```

**Note**: Ensure `data/models/kairos_base.pt` exists or the fallback training logic is enabled in `config.py`.

### 5. Run Stability Analysis (User Story 3)

Computes error metrics and statistical significance against the continuous baseline.

```bash
cd code
python main.py --mode analyze
```

**Expected Output**:
- `data/results/stats.json`: Statistical test results (p-values, confidence intervals)
- `data/results/baseline_metrics.json`: Baseline performance metrics
- Plots in `figures/`

## Configuration

Edit `code/config.py` to adjust:
- `SEED`: Random seed for reproducibility
- `QUANTIZATION_LEVEL`: 'low' (4-bit), 'medium' (8-bit), 'high' (16-bit)
- `NOISE_STD`: Standard deviation for Gaussian noise injection
- `RAM_LIMIT_MB`: Maximum allowed RAM usage (default: 7000 MB)

## Project Structure

```
.
├── code/
│ ├── main.py # Orchestration logic
│ ├── config.py # Global configuration
│ ├── data/
│ │ ├── download_libero.py # Data fetching
│ │ ├── quantize.py # Discretization logic
│ │ ├── noise.py # Noise injection
│ │ └── schema.py # Data schemas
│ ├── models/
│ │ ├── kairos_adapter.py # Model definition
│ │ ├── training_loop.py # Training logic
│ │ └── inference.py # Inference engine
│ ├── analysis/
│ │ ├── metrics.py # Error calculation
│ │ ├── stats.py # Statistical tests
│ │ └── run_baseline.py # Baseline generation
│ └── utils/
│ ├── logging.py # Logging infrastructure
│ ├── monitor.py # Resource monitoring
│ └── checkpoint.py # Graceful exit handling
├── tests/
│ ├── contract/ # Schema validation tests
│ └── integration/ # End-to-end pipeline tests
├── data/
│ ├── raw/ # Downloaded HDF5 files
│ └── processed/ # Quantized JSON outputs
├── figures/ # Generated plots
├── requirements.txt # Dependencies
└── README.md
```

## Constraints & Notes

- **CPU-Only**: No CUDA dependencies. The model must run on standard CPU hardware.
- **Real Data Only**: The pipeline fetches real data from HuggingFace. Synthetic fallbacks are disabled and will cause a hard failure if the source is unreachable.
- **Resource Limits**: The pipeline enforces a 7GB RAM limit and a 6-hour time limit via checkpointing.
- **Statistical Rigor**: Stability claims are framed as "relative degradation" using paired t-tests or Wilcoxon signed-rank tests.

## License

Internal Research Use Only.

## Contact

llmXive Research Team