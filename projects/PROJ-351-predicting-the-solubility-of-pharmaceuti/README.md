# Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## Project Overview

This project implements a machine learning pipeline to predict the aqueous solubility (logS) of pharmaceutical compounds. It compares a traditional Random Forest baseline using Morgan fingerprints against a modern Graph Neural Network (MPNN) architecture, strictly optimized for CPU execution.

## Architecture & Components

The pipeline follows a modular design separated into data processing, model training, and evaluation phases.

### 1. Data Pipeline
- **Source**: ESOL (Delaney) dataset from MoleculeNet/HuggingFace.
- **Preprocessing**: SMILES validation, invalid entry exclusion, and conversion to graph structures using RDKit.
- **Splitting**: Stratified splits based on logS quantiles to ensure distributional consistency across train/validation/test sets.
- **Key Modules**:
 - `code/data/download_esol.py`: Fetches and verifies dataset integrity.
 - `code/data/preprocess.py`: Converts raw CSV to graph data.
 - `code/data/split.py`: Generates stratified indices.

### 2. Models
- **Baseline**: Random Forest Regressor using Morgan Fingerprints (Radius=2, 2048 bits).
 - Implementation: `code/models/baseline_rf.py`
- **GNN**: Message Passing Neural Network (MPNN) with 2 layers, hidden dim 64.
 - Implementation: `code/models/gnn_mpnn.py`
 - Constraint: CPU-only execution (no CUDA).

### 3. Training & Evaluation
- **Training**:
 - `code/training/train_baseline.py`: Trains RF and logs metrics.
 - `code/training/train_gnn.py`: Trains MPNN with early stopping.
- **Evaluation**:
 - Metrics: RMSE, R², Paired T-Test, Post-hoc Power.
 - Interpretability: Node importance rankings and feature heatmaps.
 - Reports: JSON summaries and PNG visualizations.
- **Key Modules**:
 - `code/evaluation/metrics.py`: Core metric calculations.
 - `code/evaluation/statistical_test.py`: Statistical significance analysis.
 - `code/evaluation/report_generator.py`: Final report compilation.

## Directory Structure

```text
.
├── code/ # Source code
│ ├── config/ # Configuration (seeds, logging)
│ ├── data/ # Data loading, preprocessing, splitting
│ ├── models/ # Model definitions (RF, MPNN)
│ ├── training/ # Training scripts
│ ├── evaluation/ # Metrics, stats, visualization
│ ├── validation/ # Quickstart validation logic
│ └── setup_*.py # Project setup utilities
├── data/ # Data artifacts
│ ├── raw/ # Downloaded raw CSV
│ ├── processed/ # Preprocessed graphs and splits
│ └── logs/ # Execution logs
├── models/ # Saved model weights
├── results/ # Metrics, predictions, and visualizations
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quickstart Guide

### Prerequisites
- Python 3.8+
- pip

### Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### Running the Pipeline
The pipeline is executed in sequential stages. Ensure you have sufficient disk space for the dataset and logs.

1. **Download Data**:
 ```bash
 python code/data/download_esol.py
 ```
2. **Preprocess Data**:
 ```bash
 python code/data/preprocess.py
 ```
3. **Split Data**:
 ```bash
 python code/data/split.py
 ```
4. **Train Baseline (Random Forest)**:
 ```bash
 python code/training/train_baseline.py
 ```
5. **Train GNN (MPNN)**:
 ```bash
 python code/training/train_gnn.py
 ```
6. **Evaluate & Generate Report**:
 ```bash
 python code/evaluation/report_generator.py
 ```

### Validation
Run the validation script to ensure all artifacts were generated correctly:
```bash
python code/validation/quickstart_validation.py
```

## Configuration

- **Random Seeds**: Managed via `code/config/seeds.py` to ensure reproducibility.
- **Logging**: All logs are written to `data/logs/` in JSON format.
- **Hardware**: Optimized for CPU execution. GPU usage is explicitly disabled in the GNN configuration.

## Results & Outputs

Upon successful completion, the `results/` directory will contain:
- `baseline_metrics.json`: RF performance metrics.
- `gnn_metrics.json`: GNN performance metrics.
- `model_comparison.json`: Delta analysis between models.
- `gnn_predictions.csv`: Test set predictions.
- `feature_importance_*.png`: Visualizations of molecular importance.
- `final_report.json`: Comprehensive summary including statistical tests.

## License
[Insert License Information]

## Contributing
Please refer to the project's contribution guidelines.