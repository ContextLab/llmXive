# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview
This project implements a pipeline to predict molecular properties (specifically reaction barrier heights)
using descriptors generated from semi-empirical (DFTB+) and high-level DFT (Psi4) quantum chemical calculations.
It compares the accuracy and computational cost of these methods via Random Forest modeling.

## Structure
- `code/`: Python source modules
- `data/`: Raw and processed datasets (generated at runtime)
- `logs/`: Execution logs and error traces
- `reports/`: Evaluation metrics and sensitivity analysis outputs
- `specs/`: Project design documents

## Prerequisites
- Python 3.11+
- DFTB+ (for semi-empirical calculations)
- Psi4 (for high-level DFT calculations)

## Setup
1. Install dependencies: `pip install -r code/requirements.txt`
2. Configure linters: `ruff check code/` and `black code/`
3. Run the pipeline: `python code/fetch_data.py` followed by `python code/generate_descriptors.py`

## License
Internal Research Use Only