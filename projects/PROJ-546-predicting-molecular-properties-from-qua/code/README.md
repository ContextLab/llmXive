# Code Directory
This directory contains the main Python modules for the pipeline.

## Modules
- `download_data.py`: Fetches and validates raw data from Zenodo.
- `generate_descriptors.py`: Computes molecular descriptors using DFTB+ and Psi4.
- `train_models.py`: Trains Random Forest models.
- `evaluate_models.py`: Evaluates and compares model performance.
- `utils/`: Utility functions for error handling and memory monitoring.
- `validators/`: Data validation logic.

## Execution
Scripts are designed to be run from the project root:
```bash
python code/download_data.py
python code/generate_descriptors.py
```
