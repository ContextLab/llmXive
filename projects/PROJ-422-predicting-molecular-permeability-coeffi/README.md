# Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Project ID**: PROJ-422
**Status**: MVP Complete (US1, US2, US3)

## Overview

This project implements a machine learning pipeline to predict molecular permeability coefficients (or proxy targets like logP) using Graph Neural Networks (GNNs) and traditional Random Forest baselines. The pipeline ingests public chemical datasets, preprocesses molecular structures (SMILES), trains models, and performs statistical significance testing and interpretability analysis.

## Quick Start

### Prerequisites

- Python 3.11+
- `pip` (package manager)
- `git`

### Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-422-predicting-molecular-permeability-coeffi
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Generate the project directory structure:
 ```bash
 bash code/setup_dirs.sh
 ```

4. Generate the configuration file:
 ```bash
 python code/generate_config.py
 ```

### Running the Pipeline

The pipeline is executed in stages corresponding to the User Stories.

#### Stage 1: Data Ingestion & Preprocessing (US1)

Fetches the dataset, validates targets (or activates Proxy Mode), parses SMILES, and splits data.

```bash
python code/data/download.py
python code/data/preprocess.py
python code/data/split.py
```

**Outputs**:
- `data/processed/train.csv`
- `data/processed/test.csv`
- `data/processed/graph_features.csv` (for ablation)
- `results/stratification_report.md`

#### Stage 2: Model Training & Evaluation (US2)

Trains MPNN (GNN) and Random Forest models, evaluates metrics, and runs statistical tests.

```bash
python code/analysis/train.py
python code/analysis/ablation.py
python code/analysis/evaluate.py
```

**Outputs**:
- `data/interim/gnn_checkpoint.pt`
- `data/interim/rf_checkpoint.pkl`
- `results/metrics.json` (RMSE, MAE, R², p-value, Cohen's d, CI)
- `results/power_analysis.json`

#### Stage 3: Interpretability (US3)

Generates feature importance rankings using SHAP and GNNExplainer.

```bash
python code/analysis/explain.py
python code/analysis/visualize_features.py
```

**Outputs**:
- `results/feature_importance_rf.json`
- `results/feature_importance_gnn.json`
- `results/comparative_report.md`
- `results/figures/` (visualizations)

## Success Criteria Alignment

The project explicitly addresses the following Success Criteria (SC):

- **SC-001 (Performance Gap)**: Measured via RMSE reduction of GNN vs. RF baseline. Results in `results/metrics.json`.
- **SC-002 (Statistical Significance)**: Validated via paired t-test (p-value) on prediction errors.
- **SC-002b (Effect Size)**: Cohen's d calculated for the performance gap.
- **SC-002c (Confidence Intervals)**: 95% CI calculated for the mean difference.
- **SC-003 (Interpretability)**: GNN substructures ranked via GNNExplainer vs. SHAP descriptors.
- **SC-004 (Feasibility)**: Training time and memory usage logged in `results/training_log.json` (CPU-only, <6h, <7GB).
- **SC-005 (Data Integrity)**: Valid molecule retention rate (>95%) enforced in preprocessing.

## Project Structure

```
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├── code/
│ ├── data/
│ │ ├── download.py # Dataset fetching (ChEMBL v30)
│ │ ├── preprocess.py # SMILES parsing, descriptor calculation
│ │ └── split.py # Stratified/Random splitting
│ ├── models/
│ │ ├── gnn.py # MPNN architecture
│ │ └── rf.py # Random Forest implementation
│ ├── analysis/
│ │ ├── train.py # Training loop (GNN & RF)
│ │ ├── evaluate.py # Metrics & Statistical tests
│ │ ├── ablation.py # Ablation study (graph features only)
│ │ ├── explain.py # SHAP & GNNExplainer
│ │ └── visualize_features.py # Feature importance plots
│ ├── utils/
│ │ └── logging.py # Structured JSON logging
│ └── setup_directories.py # Directory setup utility
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Cleaned train/test splits
│ └── interim/ # Model checkpoints
├── results/
│ ├── metrics.json # Primary evaluation metrics
│ ├── stratification_report.md
│ ├── comparative_report.md
│ └── figures/ # Visualization outputs
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # End-to-end tests
├── config.yaml # Runtime configuration
├── requirements.txt # Dependencies
└── README.md # This file
```

## Configuration

The `config.yaml` file controls pipeline behavior:
- `bias_threshold`: Correlation threshold for bias warnings (default: 0.85).
- `retention_threshold`: Minimum valid molecule retention (default: 0.95).
- `stratification_diff_threshold`: Max allowed distribution difference for stratification.
- `proxy_target_columns`: Columns to check for Proxy Mode (e.g., 'logP').
- `staged_mode`: If `true`, allows deviations (e.g., lower retention, Proxy Mode).

## Known Limitations

- **Proxy Mode**: If experimental permeability data is missing, the pipeline may switch to predicting logP (Proxy Mode). Results in this mode are framed as feasibility checks for the GNN architecture rather than definitive permeability predictions.
- **Circular Validation**: The ablation study (T023) compares topology-only features against a descriptor-based target (logP), which is a feasibility check with acknowledged circularity.

## Contributing

Ensure all tests pass before committing:
```bash
pytest tests/
```
Format code:
```bash
black code/
ruff check code/
```