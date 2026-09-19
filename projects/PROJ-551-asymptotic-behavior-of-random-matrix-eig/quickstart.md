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
cd code
python analysis/raw_matrix_capture.py --N 1000 --seed 42
python analysis/results_recorder.py --N 1000 --seed 42 --theta 2.5
```

This will produce:
- `data/raw/matrix_N1000_seed42.npy`
- `data/processed/single_run_results.json`
- An entry in `state/metadata_registry.json`

## Full Parameter Sweep

To run the full Monte Carlo sweep across $\theta$ values:

```bash
cd code
python analysis/sweep_matrix_generator.py --grid theta
python analysis/threshold_sweep.py
python analysis/threshold_identification.py
```

This will produce:
- Raw matrices in `data/raw/sweep/`
- Aggregated results in `data/processed/mc_results.csv`
- Threshold identification in `data/processed/threshold_identification.json`
- Visualization in `data/figures/outlier_probability_vs_theta.png`

## Sensitivity Analysis

To analyze the effect of sparsity density:

```bash
cd code
python analysis/sensitivity_density_sweep.py
python analysis/sensitivity_variation.py
```

## Methodology Note: The Computational Observer

This study operates under a strictly observational framework (FR-007). It is crucial
to distinguish between the mathematical model and any potential physical interpretation.

**The "Observer"**: In the context of this research, the "observer" is the
deterministic computational algorithm (specifically, the iterative spectral solver)
that measures spectral statistics within the simulated ensemble. It is not a
physical entity, nor does it possess a "frame of reference" in the relativistic
sense.

**Probability as Algorithmic Property**: The "probability" of an outlier emerging
(e.g., $P(\text{outlier} | \theta)$) is a statistical property of the algorithm's
interaction with the generated ensemble of random matrices. It represents the
frequency of a specific spectral configuration observed by the solver across many
independent runs. It is **not** a claim about a physical stochastic process
occurring in nature.

**Limitations**: The "sparse perturbations" applied are mathematical constructs
defined by explicit rank and support density parameters. They are not physical
noise or fluctuations. No specific physical system is modeled; the findings are
confined to the mathematical ensemble defined by the Wigner semicircle law and
the applied perturbations.

## Reproducibility

All random number generators are seeded explicitly. To ensure full reproducibility:
1. Check `state/metadata_registry.json` for the exact seeds and parameters used.
2. Ensure the `requirements.txt` versions match the run environment.
3. Raw data files are checksummed (SHA-256) upon generation and stored in the registry.

## Output Artifacts

- `data/raw/`: Raw matrix instances (`.npy`)
- `data/processed/`: Aggregated results, thresholds, and fitted parameters
- `data/figures/`: Visualization plots
- `state/`: Metadata registry, logs, and validation reports
- `research.md`: Detailed theoretical background and methodology

## Troubleshooting

- **Memory Errors**: For $N > 2000$, ensure your environment has sufficient RAM.
 The project is optimized to stay under 7GB for $N=2000$.
- **Convergence Issues**: If the iterative solver fails to converge, check the
 `data/logs/simulation_run.log` for specific error codes. Increasing the
 `--max-iter` parameter in `config.py` may help.