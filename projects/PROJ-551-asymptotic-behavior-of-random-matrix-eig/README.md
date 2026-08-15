# PROJ-551: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Overview
This project investigates the asymptotic behavior of eigenvalues in large random matrices (Wigner matrices) subject to sparse deterministic perturbations. The study focuses on identifying outlier eigenvalues that emerge beyond the bulk spectrum (semicircle law) and determining the critical perturbation threshold ($\theta_c$) where phase transitions occur.

## Project Structure
- `code/`: Source code for generators, analysis, and utilities
- `data/`: Raw and processed data artifacts
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents
- `state/`: Project state management and checksums

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run a single simulation: `python code/main.py --n 1000 --theta 2.5`
3. Run the full parameter sweep: `python code/analysis/threshold_sweep.py`

## Key Findings
- Outliers emerge when perturbation strength $\theta > 1$
- Critical threshold $\theta_c$ depends on sparsity pattern
- Monte Carlo simulations confirm theoretical BBP predictions

## Reproducibility
All experiments use fixed random seeds and structured logging. Checksums for raw data are maintained in `state/checksums.json`.
