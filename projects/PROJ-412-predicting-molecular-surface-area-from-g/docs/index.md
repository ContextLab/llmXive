# llmXive: Predicting Molecular Surface Area from Graph Convolutional Networks

## Project Overview

This project implements an automated scientific pipeline to predict molecular Solvent Accessible Surface Area (SASA) using Graph Convolutional Networks (GCNs). The pipeline ingests real molecular data from ZINC15, generates 3D conformers, calculates SASA labels, trains predictive models, and performs rigorous sensitivity analysis.

## Functional Requirements Coverage

This documentation covers the implementation of all seven functional requirements (FR-001 to FR-007):

- **FR-001**: Real data ingestion from ZINC15 with streaming to avoid memory constraints
- **FR-002**: Graph construction with 2D and 3D feature extraction
- **FR-003**: 3D conformer generation using ETKDG and SASA calculation
- **FR-004**: Stratified data splitting by molecular weight with distribution validation
- **FR-005**: Model training with early stopping and memory monitoring
- **FR-006**: Sensitivity analysis on MAE thresholds with multiple-comparison correction
- **FR-007**: Reproducibility through seed management, checksum verification, and parameter logging

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd llmXive-predicting-molecular-surface-area

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt

# Install PyTorch and PyTorch Geometric
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install torch-geometric==2.4.0 --index-url https://download.pytorch.org/whl/cpu
```

### Running the Pipeline

```bash
# Run the full pipeline
python code/main.py --mode full --seed 42

# Run quickstart validation
python code/run_quickstart_validation.py
```

## Directory Structure

```
.
├── code/
│ ├── data/ # Data ingestion and preprocessing
│ ├── models/ # Model training and evaluation
│ ├── eval/ # Sensitivity analysis and metrics
│ ├── utils/ # Utility functions
│ ├── data_models/ # Data class definitions
│ ├── config.py # Configuration parameters
│ └── main.py # Main entry point
├── data/
│ ├── raw/ # Raw ingested data
│ ├── processed/ # Processed datasets
│ ├── splits/ # Train/test split indices
│ └── schemas/ # Schema definitions
├── results/
│ ├── reports/ # Analysis reports
│ ├── plots/ # Visualization plots
│ ├── baseline/ # Baseline model artifacts
│ └── predictions/ # Model predictions
├── logs/ # Execution logs
├── tests/ # Test suites
├── docs/ # API documentation (this folder)
└── README.md
```

## API Documentation

Detailed API documentation is available for each major module:

- [Data Module API](api/data.md) - Ingestion, preprocessing, and splitting
- [Models Module API](api/models.md) - GCN and baseline model training
- [Evaluation Module API](api/eval.md) - Metrics, sensitivity analysis, and reporting

## Key Features

### Real Data Sourcing
- Streams data from ZINC15 using HuggingFace `datasets` library
- Implements "Fail Loudly" principle: no synthetic fallbacks
- Validates SMILES syntax and filters molecules >100 atoms

### 3D Conformer Generation
- Uses RDKit's ETKDG method for conformer generation
- Logs all generation parameters for reproducibility
- Tracks failure reasons with standardized error codes

### Model Training
- Lightweight GCN optimized for CPU execution
- Early stopping with patience=5, max 50 epochs [UNRESOLVED-CLAIM: c_3fddb582 — status=not_enough_info]
- Dynamic batch size adjustment for OOM handling
- Memory monitoring with peak RAM logging

### Sensitivity Analysis
- Absolute threshold sweep: {0.01, 0.05, 0.1} Å² [UNRESOLVED-CLAIM: c_89aa78fa — status=not_enough_info]
- Multiple-comparison correction (Bonferroni for n≤5, FDR for n>5) [UNRESOLVED-CLAIM: c_a8d1b542 — status=not_enough_info]
- Statistical power analysis and limitations reporting

## Reproducibility

The pipeline ensures reproducibility through:
- Fixed random seeds (configurable via `--seed` argument)
- SHA-256 checksums for all data files
- Explicit parameter logging for conformer generation
- Complete provenance tracking in output artifacts

## Limitations

- **Memory Constraints**: Pipeline designed for ≤7GB RAM usage [UNRESOLVED-CLAIM: c_5e5776e8 — status=not_enough_info]
- **Dataset Size**: Processes ZINC15 subset via streaming
- **Conformer Generation**: ~5-10% failure rate expected for complex molecules [UNRESOLVED-CLAIM: c_a269b3cb — status=not_enough_info]
- **CPU-Only**: GCN training optimized for CPU (no GPU acceleration)

## Contributing

See the main README.md for contribution guidelines.

## License

[Project License]

## References

- ZINC15 Database: [irwinlab.stanford.edu/zinc15](http://zinc15.docking.org/)
- RDKit: [rdkit.org](https://www.rdkit.org/)
- PyTorch Geometric: [pytorch-geometric.readthedocs.io](https://pytorch-geometric.readthedocs.io/)
- ETKDG Method: [PubChem](https://pubchem.ncbi.nlm.nih.gov/)