# Quick Start Guide

This guide provides instructions for reproducing the full parameter sweep and sensitivity analysis for the project "Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations".

## Prerequisites

- Python 3.11+
- Required dependencies installed via `pip install -r code/requirements.txt`
- Ensure the project root is the current working directory

## Environment Setup

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Verify directory structure:
 ```bash
 ls code/
 ls data/raw/
 ls data/processed/
 ```

## Reproducing the Full Parameter Sweep (User Story 2)

The parameter sweep investigates the critical threshold $\theta_c$ by varying matrix size $N$, perturbation strength $\theta$, and random seeds.

### Step 1: Generate Raw Data with Checksums (Task T040a)

This step generates the raw Wigner matrices for the sweep grid and computes their SHA-256 checksums.

```bash
python code/analysis/sweep_matrix_generator.py
```

**Outputs:**
- Raw matrices: `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy`
- Checksum manifest: `state/checksums_sweep.json`

### Step 2: Execute the Threshold Sweep (Task T020)

This step processes the raw data, computes eigenvalues, and identifies outliers.

```bash
python code/analysis/threshold_sweep.py
```

**Outputs:**
- Aggregated results: `data/processed/threshold_sweep_results.csv`

### Step 3: Statistical Analysis and Threshold Identification (Task T021b)

This step fits a logistic regression model to determine the critical threshold $\theta_c$.

```bash
python code/analysis/threshold_analysis_runner.py
```

**Outputs:**
- Threshold identification: `data/processed/threshold_identification.json`
- Fitted parameters: `data/processed/threshold_fit_params.json`
- Final report: `data/processed/critical_threshold_report.json`

### Step 4: Visualization (Task T025)

Generate the plot of outlier probability vs. $\theta$.

```bash
python code/analysis/plot_outlier_probability.py
```

**Output:**
- Plot: `data/figures/outlier_probability_vs_theta.png`

## Reproducing the Sensitivity Analysis (User Story 3)

This analysis tests the robustness of $\theta_c$ against variations in sparsity density.

### Step 1: Execute the Density Sweep (Task T028)

Run the sensitivity analysis over sparsity densities $\{0.1, 0.2, 0.3\}$.

```bash
python code/analysis/sensitivity_density_sweep.py
```

**Output:**
- Results: `data/processed/sensitivity_density_sweep.csv`

### Step 2: Compute Threshold Variation (Task T029a)

Calculate the standard deviation of $\theta_c$ across the density sweep.

```bash
python code/analysis/sensitivity_variation.py
```

**Output:**
- Variation data: `data/processed/sensitivity_variation.csv`

### Step 3: Generate Sensitivity Report (Task T030)

```bash
python code/analysis/sensitivity_analysis.py
```

**Output:**
- Report: `data/processed/sensitivity_report.md`

## Verification

To verify the integrity of the generated data:

```bash
python code/utils/checksum.py --verify-all
```

This will validate all checksums in `state/checksums_raw.json` and `state/checksums_sweep.json`.

## Troubleshooting

- **Memory Errors**: Ensure you are not running multiple instances simultaneously. The iterative solver is designed for CPU-tractable memory usage (< 7 GB for N=2000).
- **Missing Dependencies**: If `scipy.sparse.linalg.eigsh` fails, ensure `scipy` is installed and up to date.
- **Path Errors**: Ensure you are running commands from the project root directory.

## Notes

- All scripts use deterministic random seeds defined in `code/utils/config.py` or via CLI arguments.
- The "observer" in this study is the computational algorithm measuring spectral statistics, not a physical entity.
- This project is purely observational with simulated data; no physical systems are being modeled.