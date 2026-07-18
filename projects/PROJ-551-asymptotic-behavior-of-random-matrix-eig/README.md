# PROJ-551: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Overview
This project investigates the asymptotic behavior of eigenvalues of large random matrices (Wigner matrices) under sparse deterministic perturbations. We focus on the emergence of outliers beyond the semicircle law edge and the detection of critical perturbation thresholds (BBP phase transition).

## Project Structure
- `src/`: Source code for generators, analysis, and simulation
- `data/`: Raw and processed data artifacts
- `specs/`: Feature specifications and design documents
- `tests/`: Unit and integration tests
- `scripts/`: Utility scripts for data generation and analysis

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run a single simulation: `python src/main.py --n 1000 --theta 2.5 --seed 42`
3. Run the full parameter sweep: `python scripts/run_sweep.py`

## Data Hygiene
All raw data artifacts are checksummed before aggregation. See `src/utils/checksum.py` for details.

## Observational Constraints
This study is purely observational. All findings are framed as associational correlations. No physical observer modeling is included.
