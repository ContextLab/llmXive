# Predicting Molecular Properties from Quantum Chemical Calculations

**Project ID**: PROJ-546
**Status**: Active

## Overview
This project implements a pipeline to predict molecular properties (specifically reaction barrier heights) using descriptors derived from quantum chemical calculations. It compares semi-empirical methods (DFTB+) against high-level DFT baselines (Psi4) to evaluate computational trade-offs.

## Structure
- `code/`: Python implementation scripts (data download, descriptor generation, model training, evaluation).
- `data/`: Raw datasets, processed descriptors, and model artifacts.
- `tests/`: Unit and integration tests.
- `specs/`: Feature specifications and design documents.
- `docs/`: Project documentation and reports.

## Prerequisites
- Python 3.11+
- DFTB+ (for semi-empirical calculations)
- Psi4 (for DFT calculations)
- Required Python packages listed in `code/requirements.txt`

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Download data: `python code/download_data.py`
3. Generate descriptors: `python code/generate_descriptors.py`
4. Train models: `python code/train_models.py`

## License
Academic Use Only
