# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview
This project implements a pipeline to predict molecular reaction barrier heights using semi-empirical (DFTB+) and high-level DFT (Psi4) quantum chemical calculations, followed by machine learning modeling (Random Forest) and sensitivity analysis.

## Project Structure
- `code/`: Python scripts for data download, descriptor generation, model training, and evaluation.
- `data/`: Raw and processed data files (CSV, XYZ, logs).
- `reports/`: Evaluation metrics, sensitivity analysis, and summary reports.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents and user stories.

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Download data: `python code/download_data.py`
3. Generate descriptors: `python code/generate_descriptors.py`
4. Train models: `python code/train_models.py`
5. Evaluate: `python code/evaluate_models.py`

## License
MIT
