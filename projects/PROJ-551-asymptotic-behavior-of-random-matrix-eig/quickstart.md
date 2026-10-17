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
python -m code.main --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal
```

This produces `data/processed/single_run_results.json`, a checksum entry in
`data/checksums.yaml`, and a detailed log at `data/logs/single_run.log`.

## Full Parameter Sweep (T004)

Run the theta sweep over N in {100, 500, 1000, 2000},
theta in {0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0}, seeds in {42, 123, 456, 789},
k in {1, 2, 5}, and patterns in {diagonal, block-sparse, random-sparse}:

```bash
python code/analysis/threshold_sweep.py --grid theta
```

(Further commands omitted for brevity.)

## Reproducibility

All random number generators are seeded explicitly. [UNRESOLVED-CLAIM: c_a199ecbf — status=not_enough_info] Raw matrix files are
checksummed (`data/raw/*.npy`) upon generation into `data/checksums.yaml`.
Given the same seeds and parameters, the pipeline reproduces the same
eigenvalues (CPU‑only ARPACK, `scipy.sparse.linalg.eigsh`).

## Output Artifacts

- `data/raw/`: Raw matrix instances (`.npy`) and checksum manifest
- `data/processed/`: Aggregated results, thresholds, and fitted parameters
- `data/figures/`: Visualization plots
- `data/logs/`: Run logs
- `research.md`: Detailed theoretical background and methodology

## Troubleshooting

- **Memory Errors**: `N` too large for available RAM | Reduce `--N` to ≤ 1500 or enable streaming mode (`--stream`).
- **ARPACK did not converge**: `tol` too strict or maxiter insufficient | Increase `--maxiter` (default 1000) or relax `--tol` (default 1e‑10).
- **Schema validation fails**: Output file corrupted or missing required fields | Re‑run the failing phase; ensure the corresponding schema file exists under `contracts/`.
- **Test T001 fails**: Seed mismatch or nondeterministic RNG usage | Verify that all random calls use the same `numpy.random.default_rng(seed)` instance.
