# Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## Overview

This project implements a machine learning pipeline to predict the water solubility (logS) of pharmaceutical compounds. It compares a traditional Random Forest baseline (using Morgan fingerprints) against a Message Passing Neural Network (MPNN) using Graph Neural Networks (GNNs).

## Project Structure

```
.
├── code/ # Source code
│ ├── config/ # Configuration and seeds
│ ├── data/ # Data download and preprocessing
│ ├── evaluation/ # Metrics, statistical tests, and reporting
│ ├── models/ # Model definitions (RF, GNN)
│ ├── training/ # Training scripts
│ └── validation/ # Validation utilities
├── data/ # Data artifacts
│ ├── raw/ # Raw downloaded datasets (ESOL)
│ ├── processed/ # Preprocessed graphs and splits
│ └── logs/ # Execution logs
├── models/ # Trained model checkpoints
├── results/ # Evaluation metrics, predictions, and reports
├── tests/ # Unit and integration tests
├── docs/ # Documentation (this file)
├── requirements.txt # Python dependencies
└── README.md # Project overview
```

## Prerequisites

- Python 3.8+
- pip package manager

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

**Note**: This project is configured for **CPU-only** execution. Ensure you do not have CUDA/GPU dependencies forced unless you modify the training scripts.

## Usage

### 1. Data Preparation

Download and preprocess the ESOL dataset:

```bash
# Download raw data
python code/data/download_esol.py

# Preprocess data (SMILES parsing, feature extraction)
python code/data/preprocess.py

# Split data into train/validation/test sets
python code/data/split.py
```

### 2. Baseline Model (Random Forest)

Train the Random Forest baseline using Morgan fingerprints:

```bash
python code/training/train_baseline.py
```

*Output*: `models/baseline_rf.pkl`, `results/baseline_metrics.json`

### 3. GNN Model (MPNN)

Train the Message Passing Neural Network:

```bash
python code/training/train_gnn.py
```

*Output*: `models/gnn_mpnn.pt`, `results/gnn_metrics.json`, `results/gnn_predictions.csv`

### 4. Evaluation and Analysis

Run statistical comparison and generate reports:

```bash
# Compare models
python code/evaluation/compare_models.py

# Run statistical significance tests
python code/evaluation/statistical_test.py

# Generate interpretability visualizations
python code/evaluation/interpretability.py

# Generate final summary report
python code/evaluation/report_generator.py
```

## Key Components

- **Data Pipeline**:
 - `code/data/download_esol.py`: Fetches ESOL dataset from MoleculeNet/HuggingFace.
 - `code/data/preprocess.py`: Converts SMILES to graph representations using RDKit.
 - `code/data/split.py`: Stratified split based on logS quantiles.

- **Models**:
 - `code/models/baseline_rf.py`: Random Forest with 2048-bit Morgan fingerprints.
 - `code/models/gnn_mpnn.py`: Simplified MPNN (2 layers, hidden_dim=64) for CPU efficiency.

- **Evaluation**:
 - `code/evaluation/metrics.py`: Calculates RMSE and R².
 - `code/evaluation/statistical_test.py`: Paired t-test and power analysis.
 - `code/evaluation/interpretability.py`: Node importance heatmaps.

## Reproducibility

Random seeds are pinned globally via `code/config/seeds.py`. Ensure `code/training/set_seeds.py` is executed before any training or data loading steps to guarantee bit-for-bit reproducibility.

## Constraints & Design Decisions

- **CPU-Only**: All GNN training is restricted to CPU to ensure compatibility with standard cloud instances.
- **Memory Efficiency**: Data preprocessing streams chunks to avoid OOM errors on large datasets.
- **Real Data Only**: The pipeline strictly uses the ESOL dataset. Synthetic fallbacks are disabled to ensure scientific validity.
- **Time Limits**: GNN training is designed to converge within 6 hours on a 2-core CPU.

## License

[Insert License Information Here]

## Contributing

Please read the contributing guidelines before submitting pull requests.
