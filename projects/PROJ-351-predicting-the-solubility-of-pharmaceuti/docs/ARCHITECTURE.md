# Architecture Document: ESOL Solubility Prediction Pipeline

## 1. System Overview

This document details the architectural decisions, data flow, and module interactions for the ESOL Solubility Prediction Pipeline. The system is designed to be reproducible, modular, and strictly CPU-executable.

## 2. Design Principles

- **Reproducibility**: All random seeds are pinned globally before data loading.
- **Fail Loudly**: Data loaders must raise exceptions on network failure; no synthetic fallbacks.
- **CPU-First**: All models are optimized for CPU inference and training.
- **Streaming**: Large datasets are processed in chunks to respect memory constraints (~7GB RAM).
- **Modularity**: Distinct separation between data, model, training, and evaluation logic.

## 3. Data Flow

1. **Ingestion**: `download_esol.py` fetches the ESOL dataset from HuggingFace/MoleculeNet.
 - Validates checksum.
 - Saves to `data/raw/esol.csv`.
2. **Preprocessing**: `preprocess.py` reads the raw CSV.
 - Validates SMILES strings using RDKit.
 - Excludes invalid entries (logged to `data/logs/exclusions.log`).
 - Converts valid molecules to graph representations (atom/bond features).
 - Saves processed graphs to `data/processed/`.
3. **Splitting**: `split.py` performs a stratified split on logS values.
 - Generates train/val/test indices.
 - Saves indices to `data/processed/splits.json`.
4. **Training**:
 - **Baseline**: `train_baseline.py` loads processed data, generates Morgan fingerprints, trains a Random Forest, and saves the model.
 - **GNN**: `train_gnn.py` loads graph data, trains the MPNN with early stopping, and saves the best checkpoint.
5. **Evaluation**:
 - `metrics.py` calculates RMSE and R².
 - `statistical_test.py` performs paired t-tests.
 - `interpretability.py` generates visualizations.
 - `report_generator.py` compiles all results into a final report.

## 4. Module Specifications

### 4.1 Data Layer (`code/data/`)
- **download_esol.py**: Handles external data fetching and integrity verification.
- **preprocess.py**: Handles SMILES parsing and graph construction. Implements chunked processing.
- **split.py**: Handles dataset stratification.

### 4.2 Model Layer (`code/models/`)
- **baseline_rf.py**: Implements Random Forest logic using `scikit-learn` and `rdkit`.
- **gnn_mpnn.py**: Implements the MPNN architecture using `torch_geometric`.
 - Layers: 2 Message Passing layers.
 - Hidden Dimension: 64.
 - Activation: ReLU.

### 4.3 Training Layer (`code/training/`)
- **train_baseline.py**: Orchestrates RF training pipeline.
- **train_gnn.py**: Orchestrates GNN training with early stopping and timer logging.

### 4.4 Evaluation Layer (`code/evaluation/`)
- **metrics.py**: Standard regression metrics.
- **statistical_test.py**: Hypothesis testing (t-test, power analysis).
- **interpretability.py**: Node importance calculation and plotting.
- **report_generator.py**: Aggregates results for final reporting.

### 4.5 Configuration (`code/config/`)
- **seeds.py**: Centralized seed management.
- **logging_config.py**: JSON logging setup.

## 5. Error Handling Strategy

- **Data Fetch Failures**: Raise `ConnectionError` or `ValueError` immediately. No retries with synthetic data.
- **SMILES Parsing Failures**: Log count to `exclusions.log` and continue with valid data.
- **Training Non-Convergence**: Detect if validation loss plateaus/increases for >20 epochs; save best checkpoint and log warning.

## 6. Performance Constraints

- **Time**: All tasks must complete within 6 hours on a 2-core CPU.
- **Memory**: Preprocessing and training must stream data or use chunking to stay under ~7GB RAM.
- **Accuracy**: Baseline R² > 0.9 triggers a "ceiling effect" flag in the final report.

## 7. Future Considerations

- Potential integration with GPU backends if hardware constraints are relaxed.
- Expansion to other solubility datasets (e.g., FreeSolv).
- Enhanced interpretability methods (SHAP, LIME).
