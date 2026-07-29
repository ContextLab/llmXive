# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview
This project implements a pipeline to predict molecular barrier heights using semi-empirical (DFTB+) and high-level DFT (Psi4) descriptors, comparing their accuracy and computational cost.

## Structure
- `specs/`: Project specifications and user stories
- `data/`: Raw and processed data artifacts
- `code/`: Python implementation scripts and utilities
- `tests/`: Test suite

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Download data: `python code/download_data.py`
3. Generate semi-empirical descriptors: `python code/generate_descriptors.py --method dftb`
4. Train and evaluate models: `python code/train_models.py`

## Requirements
- Python 3.11+
- DFTB+ (system installation)
- Psi4 (system installation)
