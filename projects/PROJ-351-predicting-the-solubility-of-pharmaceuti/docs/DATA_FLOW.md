# Data Flow Documentation

This document describes the movement and transformation of data through the pipeline.

## Input Source

- **Dataset**: ESOL (Delaney) Solubility Dataset
- **Source**: MoleculeNet Repository
- **Format**: CSV (SMILES, logS, other molecular descriptors)
- **Location**: `data/raw/esol.csv`

## Processing Stages

### Stage 1: Validation & Cleaning
- **Input**: Raw CSV
- **Process**:
 - Parse SMILES using RDKit.
 - Filter out molecules with invalid SMILES.
 - Remove rows with missing `logS` values.
- **Output**: Cleaned DataFrame (in memory or temporary file).
- **Logs**: Exclusion counts written to `data/logs/exclusions.log`.

### Stage 2: Feature Extraction
- **Input**: Cleaned SMILES
- **Process**:
 - Generate atom features (atomic number, degree, hybridization, etc.).
 - Generate bond features (bond type, conjugation, etc.).
 - Construct graph objects.
- **Output**: Processed graph data saved to `data/processed/`.

### Stage 3: Splitting
- **Input**: Processed Graphs
- **Process**:
 - Stratified split based on `logS` quantiles.
 - Generate train/validation/test indices.
- **Output**: Split indices saved to `data/processed/splits.json`.

### Stage 4: Model Training
- **Input**: Training split graphs
- **Process**:
 - Convert graphs to tensors (PyTorch Geometric Data objects).
 - Train Random Forest or MPNN.
- **Output**: Serialized model files (`models/*.pkl`, `models/*.pt`).

### Stage 5: Evaluation
- **Input**: Test split graphs + Trained Models
- **Process**:
 - Generate predictions.
 - Calculate RMSE and R².
 - Perform statistical significance testing.
- **Output**:
 - `results/gnn_predictions.csv`
 - `results/baseline_metrics.json`
 - `results/gnn_metrics.json`
 - `results/model_comparison.json`
 - `results/final_report.json`
 - `results/feature_importance_*.png`

## Output Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Raw CSV | `data/raw/esol.csv` | Original dataset |
| Exclusion Log | `data/logs/exclusions.log` | Details of removed data |
| Split Indices | `data/processed/splits.json` | Train/Val/Test masks |
| Baseline Model | `models/baseline_rf.pkl` | Random Forest weights |
| GNN Model | `models/gnn_mpnn.pt` | PyTorch Geometric model |
| Metrics | `results/*.json` | Performance statistics |
| Visualizations | `results/*.png` | Feature importance plots |
