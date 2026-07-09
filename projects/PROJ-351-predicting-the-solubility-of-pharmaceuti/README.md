# Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## Project Overview

This project implements a machine learning pipeline to predict the aqueous solubility (logS) of pharmaceutical compounds. It compares a Random Forest baseline using Morgan fingerprints against a Message Passing Neural Network (MPNN) using Graph Neural Networks (GNNs).

## Features

- **Data Pipeline**: Automated download and cleaning of the ESOL dataset from MoleculeNet.
- **Preprocessing**: Conversion of SMILES strings to molecular graphs using RDKit and extraction of atom/bond features.
- **Baseline Model**: Random Forest regression using Morgan fingerprints (Radius 2, 2048 bits).
- **GNN Model**: Custom Message Passing Neural Network (MPNN) implemented in PyTorch Geometric, optimized for CPU execution.
- **Evaluation**: Comprehensive metrics (RMSE, R²) and statistical significance testing (paired t-test, power analysis).
- **Interpretability**: Feature importance analysis and visualization of node contributions.

## Requirements

- Python 3.10+
- See `requirements.txt` for the full list of dependencies.

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-name>
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Source code modules
│ ├── config/ # Configuration and seed management
│ ├── data/ # Data download and preprocessing scripts
│ ├── evaluation/ # Metrics, statistical tests, and reporting
│ ├── models/ # Model definitions (RF, MPNN)
│ ├── training/ # Training loops and logging utilities
│ └── setup_*.py # Project setup and environment checks
├── data/ # Data storage
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Preprocessed graphs and split indices
├── models/ # Trained model checkpoints
├── results/ # Evaluation metrics, plots, and reports
├── tests/ # Unit and integration tests
├── docs/ # Documentation (this file)
├── requirements.txt # Python dependencies
└── README.md # Project documentation
```

## Usage

### 1. Download and Preprocess Data

Run the data pipeline to download the ESOL dataset, clean invalid SMILES, and generate graph representations:

```bash
python code/data/download_esol.py
python code/data/preprocess.py
python code/data/split.py
```

### 2. Train Baseline Model (Random Forest)

Train the Random Forest baseline using Morgan fingerprints:

```bash
python code/training/train_baseline.py
```

This will save the model to `models/` and metrics to `results/baseline_metrics.json`.

### 3. Train GNN Model (MPNN)

Train the Message Passing Neural Network:

```bash
python code/training/train_gnn.py
```

This script includes early stopping and saves the model to `models/` and metrics to `results/gnn_metrics.json`.

### 4. Evaluation and Reporting

Run statistical tests and generate the final report:

```bash
python code/evaluation/statistical_test.py
python code/evaluation/report_generator.py
```

Visualizations and interpretability reports are saved in `results/`.

## Configuration

- **Random Seeds**: Controlled via `code/config/seeds.py`. Ensure reproducibility by setting the seed environment variable or modifying the config.
- **Logging**: All training and exclusion logs are written to `data/logs/`.

## Testing

Run the test suite to verify the pipeline:

```bash
pytest tests/
```

## License

[Insert License Information Here]

## Acknowledgments

- ESOL Dataset from MoleculeNet
- RDKit for cheminformatics
- PyTorch Geometric for GNN implementation
