# Quickstart Guide: Asymptotic Behavior of Random Matrix Eigenvalues

## Overview

This project investigates the asymptotic behavior of eigenvalues in large random matrices
subjected to sparse perturbations. The core objective is to empirically verify the
BBP (Baik-Ben Arous-Péché) phase transition threshold $\theta_c$ and analyze the
sensitivity of this threshold to the sparsity density of the perturbation.

## Prerequisites

- Python 3.9+
- Dependencies listed in `code/requirements.txt`

## Installation

```bash
cd code
pip install -r requirements.txt
```

## Quick Run (Single Instance)

To generate a single Wigner matrix instance and analyze its spectrum:

```bash
python code/main.py --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal
```

This produces `data/processed/single_run_results.json`.

## Full Parameter Sweep (T002)

Run the theta sweep over N in {100, 500, 1000, 2000},
theta in {0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0}, seeds in {42, 123, 456, 789},
k in {1, 2, 5}, and patterns in {diagonal, block-sparse, random-sparse}:

```bash
python code/analysis/threshold_sweep.py --grid theta
```

This produces:
- Raw checksummed matrices in `data/raw/sweep/` (with `checksums.json`)
- `data/processed/mc_results.csv` (1008 rows, one real ARPACK result per run)
- `data/processed/convergence_data.json` (per-N bulk-edge convergence to ±2.0)
- Logs in `data/logs/threshold_sweep.log`

## Sensitivity Analysis

To analyze the effect of sparsity density (later phases):

```bash
python code/analysis/sensitivity_density_sweep.py
python code/analysis/sensitivity_variation.py
```

## Methodology Note: The Computational Observer

This study operates under a strictly observational framework (FR-007). The "observer"
is the deterministic computational algorithm (the iterative spectral solver) that
measures spectral statistics of the seeded mathematical ensemble. No physical system
is modeled; the random matrices are controlled, reproducible mathematical constructs,
and all findings are associational statements about that ensemble.

## Reproducibility

All random number generators are seeded explicitly. Raw matrix files are
checksummed (SHA-256) upon generation into `data/raw/sweep/checksums.json`.
Given the same seeds and parameters, the pipeline reproduces the same
eigenvalues (CPU-only ARPACK, `scipy.sparse.linalg.eigsh`).

## Output Artifacts

- `data/raw/`: Raw matrix instances (`.npy`) and checksum manifest
- `data/processed/`: Aggregated results, thresholds, and fitted parameters
- `data/figures/`: Visualization plots
- `data/logs/`: Run logs
- `research.md`: Detailed theoretical background and methodology

## Troubleshooting

- **Memory Errors**: The sweep is optimized to stay under 7 GB for N=2000. [UNRESOLVED-CLAIM: c_e147bc37 — status=not_enough_info]
- **Convergence Issues**: See `data/logs/threshold_sweep.log`; the ARPACK
 tolerance is set in `code/analysis/threshold_sweep.py` (`EIGSH_TOL`).