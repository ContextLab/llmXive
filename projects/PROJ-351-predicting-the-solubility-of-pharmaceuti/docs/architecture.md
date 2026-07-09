# Architecture Documentation

## System Overview

The project follows a modular pipeline architecture designed for reproducibility and extensibility. The flow is strictly linear: Data Ingestion → Preprocessing → Model Training → Evaluation → Reporting.

## Component Architecture

### 1. Data Ingestion (`code/data/`)

- **download_esol.py**: Fetches the raw ESOL dataset from the canonical source (MoleculeNet/HuggingFace). Validates the `logS` column presence.
- **preprocess.py**: Uses RDKit to parse SMILES. Filters out invalid molecules and NaN values. Extracts atom/bond features and serializes graphs to `data/processed/`.
- **split.py**: Performs stratified splitting based on `logS` quantiles to ensure distribution parity across train/val/test sets.

### 2. Model Definitions (`code/models/`)

- **baseline_rf.py**: Implements a Random Forest regressor. Uses Morgan Fingerprints (radius=2, 2048 bits) as input features.
- **gnn_mpnn.py**: Defines the `GNNMPNN` class using PyTorch Geometric. Implements a Message Passing Neural Network with configurable hidden dimensions and message functions. Optimized for CPU execution (no CUDA).

### 3. Training (`code/training/`)

- **train_baseline.py**: Orchestrates the RF training loop, handles data loading, and saves the model artifact.
- **train_gnn.py**: Orchestrates the MPNN training loop with early stopping based on validation loss.

### 4. Evaluation (`code/evaluation/`)

- **metrics.py**: Calculates RMSE and R² scores.
- **statistical_test.py**: Performs paired t-tests on prediction errors and calculates post-hoc statistical power.
- **interpretability.py**: Generates node importance rankings and heatmaps for sample molecules.
- **report_generator.py**: Aggregates all metrics into a final summary table.
- **ceiling_effect.py**: Detects if the baseline performance exceeds a threshold (R² > 0.95), indicating a potential ceiling effect.

### 5. Configuration & Utilities (`code/config/`, `code/setup_*.py`)

- **seeds.py**: Manages random seeds for `numpy`, `random`, and `torch` to ensure reproducibility.
- **setup_logging.py**: Configures the logging infrastructure to capture metrics and exclusion counts.

## Data Flow

1. **Raw Data**: `data/raw/esol.csv` (Downloaded)
2. **Processed Data**: `data/processed/graphs.json` (Graph representations)
3. **Splits**: `data/processed/splits.json` (Indices)
4. **Models**: `models/baseline.pkl`, `models/gnn.pt`
5. **Results**: `results/baseline_metrics.json`, `results/gnn_metrics.json`, `results/final_report.txt`

## Dependencies

- **Cheminformatics**: `rdkit`
- **Deep Learning**: `torch` (CPU), `torch-geometric` (CPU)
- **Data Science**: `pandas`, `numpy`, `scikit-learn`
- **Visualization**: `matplotlib`
