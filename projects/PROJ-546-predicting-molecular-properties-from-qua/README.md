# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview
This project implements a pipeline to predict molecular properties (specifically reaction barrier heights) using semi-empirical (DFTB+) and high-level DFT (Psi4) quantum chemical calculations, followed by machine learning modeling.

## Project Structure
- `code/`: Source code for data downloading, descriptor generation, model training, and evaluation.
- `data/`: Raw and processed datasets, including downloaded CSVs and generated descriptors.
- `tests/`: Unit and integration tests for the pipeline components.
- `specs/`: Feature specifications and design documents.
- `figures/`: Generated plots and visualizations.

## Prerequisites
- Python 3.11+
- DFTB+ (for semi-empirical calculations)
- Psi4 (for high-level DFT calculations)
- RDKit (for molecular handling)

## Setup
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
2. Ensure DFTB+ and Psi4 are installed and accessible in your PATH.

## Usage
See `code/` scripts for individual pipeline steps:
- `download_data.py`: Fetch experimental barrier dataset from Zenodo.
- `generate_descriptors.py`: Compute HOMO/LUMO/Mayer descriptors.
- `train_models.py`: Train Random Forest models.
- `evaluate_models.py`: Compare model performance.

## License
MIT License
