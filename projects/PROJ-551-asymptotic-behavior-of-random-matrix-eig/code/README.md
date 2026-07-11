# PROJ-551: Asymptotic Behavior of Random Matrix Eigenvalues

## Overview
This module implements the simulation and analysis of eigenvalue outliers in perturbed Wigner matrices.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the main simulation: `python main.py`

## Structure
- `generators/`: Matrix generation logic (Wigner, Perturbations)
- `analysis/`: Eigenvalue computation, threshold sweeping, sensitivity analysis
- `utils/`: Configuration, checksums, logging helpers
- `data_models.py`: Pydantic data structures
