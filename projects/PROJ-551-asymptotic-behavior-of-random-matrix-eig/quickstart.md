# Quick Start Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
cd projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig
pip install -r code/requirements.txt
```

## Running a Single Simulation
Generate a Wigner matrix with a rank-1 sparse perturbation and compute eigenvalues:
```bash
python code/main.py --n 1000 --theta 2.5 --seed 42
```
Output: `data/processed/single_run_results.json`

## Running the Full Parameter Sweep
Execute a grid search over matrix sizes $N \in [500, 2000]$ and perturbation strengths $\theta \in [1.0, 3.0]$:
```bash
python code/analysis/threshold_sweep.py
```
Output: `data/processed/threshold_sweep_results.csv`

## Reproducing Results
1. Verify data integrity: `python code/utils/checksum.py verify`
2. Re-run Monte Carlo simulations: `python code/analysis/monte_carlo_runner.py`
3. Generate sensitivity report: `python code/analysis/sensitivity_analysis.py`

## Troubleshooting
- If memory errors occur, reduce `--n` or use `--streaming` mode
- Ensure `data/raw/` has sufficient disk space for matrix storage
- Check `data/logs/simulation_run.log` for detailed error messages
