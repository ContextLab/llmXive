# Architecture Documentation

## System Overview

The system follows a modular pipeline architecture designed for reproducibility and scientific rigor. It separates concerns into distinct stages: Data Ingestion, Preprocessing, Model Training, and Evaluation.

## Data Flow

1. **Ingestion**: `download_esol.py` retrieves the raw ESOL dataset.
2. **Validation**: Raw CSV is validated for `logS` presence and checksum integrity.
3. **Preprocessing**: `preprocess.py` parses SMILES, validates molecules with RDKit, and extracts atom/bond features. Invalid entries are logged and excluded.
4. **Splitting**: `split.py` performs stratified splitting based on logS quantiles to ensure distributional consistency across splits.
5. **Training**:
 - **Baseline**: `train_baseline.py` trains a Random Forest on fingerprint vectors.
 - **GNN**: `train_gnn.py` trains an MPNN on graph tensors.
6. **Evaluation**: Metrics are calculated, statistical tests performed, and visualizations generated.

## Module Responsibilities

### `code/config/`
- `seeds.py`: Centralized seed management for `numpy`, `random`, and `torch`.

### `code/data/`
- `download_esol.py`: Handles external API calls and checksum verification.
- `preprocess.py`: Heavy lifting for molecular graph construction. Includes error handling for malformed SMILES.
- `split.py`: Logic for deterministic data partitioning.

### `code/models/`
- `baseline_rf.py`: Wrapper for `sklearn.ensemble.RandomForestRegressor`.
- `gnn_mpnn.py`: PyTorch Geometric implementation of a Message Passing Neural Network.

### `code/training/`
- `train_baseline.py`: Orchestrates RF training loop and logging.
- `train_gnn.py`: Orchestrates MPNN training with early stopping and checkpointing.

### `code/evaluation/`
- `metrics.py`: Standard regression metrics (RMSE, R²).
- `statistical_test.py`: Implements paired t-tests and power analysis.
- `interpretability.py`: Generates feature importance plots.
- `report_generator.py`: Aggregates all results into a final JSON/Text report.

## Logging Strategy

All modules utilize a centralized logging configuration (`code/config/logging_config.py`). Logs are written to `data/logs/` in JSON format with timestamps, facilitating debugging and audit trails.

## Error Handling

- **Data Fetch Failures**: Scripts raise exceptions immediately if the real data source is unreachable (no synthetic fallbacks).
- **Molecule Parsing Errors**: Invalid SMILES are logged to `data/logs/exclusions.log` and excluded from the dataset.
- **Non-Convergence**: GNN training detects non-convergence and saves the best checkpoint while logging a warning.

## Extensibility

New models can be added by implementing the `code/models/` interface. New evaluation metrics can be added to `code/evaluation/metrics.py` without modifying training logic.
