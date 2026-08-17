# Quick Start Guide

## Overview

This project investigates the asymptotic behavior of eigenvalues of random matrices under sparse perturbations. It generates Wigner matrices, applies deterministic sparse perturbations, and analyzes the emergence of outliers (eigenvalues outside the bulk spectral support) to empirically determine the critical threshold $\theta_c$.

## Prerequisites

- Python 3.11+
- `pip` for dependency management
- 7GB+ available RAM (for $N=2000$ simulations)
- 14GB+ available disk space for data artifacts

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

```bash
cd code
pip install -r requirements.txt
```

3. Ensure all required directories exist (run once):

```bash
cd code
python -c "from utils.config import ensure_directories; ensure_directories()"
```

## Reproducing the Full Parameter Sweep

The full parameter sweep systematically varies matrix size $N$ and perturbation strength $\theta$ to map the phase transition boundary.

### Step 1: Generate Raw Sweep Matrices (T040a)

This step generates and saves raw Wigner matrix instances for the full parameter grid.

```bash
cd code
python analysis/sweep_matrix_generator.py
```

**Output**: `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy`

### Step 2: Compute Sweep Checksums (T040b)

This step computes SHA-256 checksums for all generated raw matrices to ensure data integrity.

```bash
cd code
python analysis/sweep_checksums.py
```

**Output**: `state/checksums_sweep.json`

### Step 3: Run Threshold Sweep Analysis (T020)

This orchestrator executes the full sweep, ingesting the checksummed raw data and managing iterations.

```bash
cd code
python analysis/threshold_sweep.py
```

**Output**: Aggregated results used for downstream analysis.

### Step 4: Run Monte Carlo Simulation (T021a)

This step runs a sufficient number of Monte Carlo iterations per configuration to estimate outlier probabilities.

```bash
cd code
python analysis/monte_carlo_runner.py
```

**Output**: `data/processed/mc_results.csv`

### Step 5: Analyze Threshold Identification (T021b)

This step prepares the Monte Carlo results for threshold fitting.

```bash
cd code
python analysis/threshold_identification_raw.py
```

**Output**: `data/processed/threshold_identification_raw.json`

### Step 6: Fit Critical Threshold (T022a, T022b, T022c)

This step fits a sigmoid curve to the outlier probability data to estimate $\theta_c$.

```bash
cd code
python analysis/threshold_fit.py
```

**Output**: `data/processed/threshold_fit_params.json`

### Step 7: Aggregate Sweep Results (T024)

This step generates the final aggregated results file.

```bash
cd code
python analysis/threshold_sweep_aggregator.py
```

**Output**: `data/processed/threshold_sweep_results.csv`

### Step 8: Visualize Outlier Probability (T025)

This step generates a plot of the probability of outlier emergence vs. $\theta$.

```bash
cd code
python analysis/plot_outlier_probability.py
```

**Output**: `data/figures/outlier_probability_vs_theta.png`

## Sensitivity Analysis of Sparsity Thresholds

This analysis examines the robustness of $\theta_c$ to changes in sparsity density $p$.

### Step 1: Run Sensitivity Density Sweep (T027, T028)

This step sweeps over support density set $\{0.1, 0.2, 0.3\}$ for each sparsity pattern type.

```bash
cd code
python analysis/sensitivity_density_sweep.py
```

**Output**: `data/processed/sensitivity_density_sweep.csv`

### Step 2: Run Sensitivity Analysis (T027)

This step performs the core sensitivity analysis logic.

```bash
cd code
python analysis/sensitivity_analysis.py
```

**Output**: `data/processed/sensitivity_variation.csv`

### Step 3: Generate Sensitivity Report (T030)

This step generates the final markdown report stating stability or shift magnitude.

```bash
cd code
python analysis/threshold_comparison.py
```

**Output**: `data/processed/sensitivity_report.md`

## Single Run Mode (User Story 1)

For quick verification, run a single simulation instance.

```bash
cd code
python main.py --N 1000 --theta 2.5 --seed 42
```

**Outputs**:
- Raw matrix: `data/raw/matrix_N1000_seed42.npy`
- Checksum: `state/checksums_raw.json`
- Results: `data/processed/single_run_results.json`
- Logs: `data/logs/simulation_run.log`

## Verification of Edge Cases (T031)

Verify semicircle law compliance for the unperturbed (rank-0) case.

```bash
cd code
python analysis/edge_case_rank0.py
```

**Output**: `data/logs/edge_case_rank0.log`

## Configuration

All simulation parameters (seeds, tolerances, matrix sizes) can be configured via `code/config.yaml` or command-line arguments. See `code/utils/config.py` for available options.

## Troubleshooting

- **Memory Error**: Ensure you have at least 7GB RAM for $N=2000$. Use smaller $N$ for testing.
- **Convergence Failure**: If the iterative solver fails to converge, check the tolerance settings in `config.yaml` or increase the maximum iterations.
- **Missing Data**: If output files are missing, ensure all prerequisite steps (e.g., raw matrix generation) have completed successfully.

## Data Hygiene

This project adheres to Constitution Principle III (Data Hygiene). All raw data is checksummed before processing. Verify integrity using:

```bash
cd code
python utils/checksum.py --verify
```