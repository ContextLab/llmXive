# Predicting Molecular Dipole Moments with Graph Neural Networks

This project implements a computational pipeline to predict molecular dipole moments
using graph neural networks trained on quantum mechanical data from the QM9 dataset.

## Project Structure

```
projects/001-predicting-molecular-dipole-moments/
├── code/ # Python implementation modules
│ ├── data/ # Data download and preprocessing
│ ├── models/ # GNN and baseline model architectures
│ ├── training/ # Training and evaluation pipelines
│ ├── attribution/ # Feature attribution methods
│ ├── analysis/ # Statistical analysis and validation
│ └── utils/ # Utility functions
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Contract tests for schemas
├── data/ # Data storage
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Preprocessed feature matrices
│ └── checkpoints/ # Model checkpoints
├── state/ # Pipeline state tracking
├── specs/ # Feature specifications
│ └── 001-predicting-molecular-dipole-moments/
└── results/ # Generated results and figures
 └── figures/ # Visualization outputs
```

## Quick Start

1. Run the setup script to initialize project structure:
 ```bash
 python setup_project.py
 ```

2. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

3. Run tests:
 ```bash
 pytest tests/
 ```

## Requirements

- Python 3.11+
- See `code/requirements.txt` for full dependency list

## License

MIT License
