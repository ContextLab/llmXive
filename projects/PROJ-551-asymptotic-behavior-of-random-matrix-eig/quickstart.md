# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository.
2. Navigate to the project root.
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Simulation
1. Generate a single Wigner matrix with perturbation:
 ```bash
 python code/main.py --N 1000 --theta 2.5 --seed 42
 ```
2. Run a parameter sweep:
 ```bash
 python code/analysis/threshold_sweep.py --N_min 500 --N_max 2000 --theta_min 1.0 --theta_max 3.0
 ```

## Output
- Raw matrices: `data/raw/`
- Processed results: `data/processed/`
- Logs: `data/logs/`
- Figures: `figures/`

## Reproducibility
- All runs are logged with timestamps and random seeds.
- Raw data is checksummed before processing.
- Use `--seed` to ensure reproducibility.
