# Architecture Documentation

## Pipeline Flow
1. **Ingestion (`code/data/ingestion.py`)**
 - Fetches raw data from NIST/PubChem.
 - Parses SMILES into `PolymerGraph` objects.
 - Cleans data (removes missing values, handles duplicates).
 - Outputs: `data/processed/polymers.h5`.

2. **Preprocessing (`code/data/preprocessing.py`)**
 - Extracts node/edge features from graphs.
 - Computes Murcko scaffolds for splitting.
 - Performs scaffold-based train/val/test split.

3. **Modeling (`code/models/`)**
 - **GNN (`gnn.py`)**: Message-passing neural network with float32 precision.
 - **Baselines (`baselines.py`)**:
 - Random Forest with ECFP4 fingerprints.
 - Linear Regression with RDKit descriptors.
 - **Trainer (`trainer.py`)**: Handles training loops, early stopping, and gradient clipping.

4. **Evaluation (`code/evaluation/`)**
 - **Metrics (`metrics.py`)**: Computes R², MAE, Pearson correlation.
 - **Stats (`stats.py`)**:
 - Wilcoxon signed-rank test for model comparison.
 - VIF analysis for descriptor multicollinearity.
 - Sensitivity analysis sweep.
 - **Report (`report.py`)**: Generates final JSON/Markdown reports.

## Key Design Decisions
- **CPU-Only**: All models are designed to run on CPU (no GPU dependencies).
- **Real Data Only**: Strict enforcement of FR-001; no synthetic fallbacks.
- **Scaffold Split**: Ensures generalization to unseen chemical structures.
- **Float32 Precision**: Required for compatibility and stability on CPU.

## Configuration
Environment variables used throughout the pipeline:
- `SEED`: Random seed for reproducibility (default: 42).
- `EXCLUDE_SMALL_MOLS`: If "true", excludes molecules with MW < 1000 Da.
- `SACFOLD_CUTOFF`: Similarity threshold for Murcko scaffold clustering.
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR).
