# Predicting Molecular Properties from Quantum Chemical Calculations

**Project ID**: PROJ-546

## Overview
This project implements a pipeline to predict molecular properties (specifically reaction barrier heights) using semi-empirical quantum chemical descriptors (DFTB+) and high-level DFT baselines (Psi4), validated against experimental data.

## Structure
- `code/`: Python implementation scripts for data download, descriptor generation, model training, and evaluation.
- `data/`: Storage for raw and processed data artifacts.
- `tests/`: Unit and integration tests.
- `reports/`: Generated evaluation and sensitivity analysis reports.
- `logs/`: Execution logs and error tracking.
- `docs/`: Project documentation.

## Quick Start
1. Ensure Python 3.11+ is installed.
2. Install dependencies: `pip install -r code/requirements.txt`
3. Download data: `python code/download_data.py`
4. Generate descriptors: `python code/generate_descriptors.py`
5. Train and evaluate models: `python code/train_models.py` && `python code/evaluate_models.py`

## Requirements
- DFTB+ (for semi-empirical calculations)
- Psi4 (for DFT calculations)
- Python 3.11+
- scikit-learn, pandas, rdkit

## License
Proprietary - Internal Research Use Only
