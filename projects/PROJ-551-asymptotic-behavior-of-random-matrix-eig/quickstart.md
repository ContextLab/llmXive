# Quickstart Guide: Asymptotic Behavior of Random Matrix Eigenvalues

This guide provides instructions for reproducing the full parameter sweep and sensitivity analysis for the study on the asymptotic behavior of random matrix eigenvalues with sparse perturbations.

## Prerequisites

Ensure you have Python 3.11+ installed. Install the required dependencies:

```bash
cd code
pip install -r requirements.txt
```

## Project Structure

- `code/`: Source code for generators, analysis, and utilities
- `data/raw/`: Raw matrix data (checksummed)
- `data/processed/`: Processed results and analysis outputs
- `data/figures/`: Generated plots and visualizations
- `state/`: State files including checksums and logs
- `tests/`: Unit and integration tests

## Reproducing the Full Parameter Sweep

The parameter sweep (User Story 2) systematically varies perturbation norms and dimensions to determine the critical threshold $\theta_c$.

### Step 1: Generate and Checksum Raw Matrices

First, generate the raw Wigner matrices for the sweep grid and compute their checksums. This is handled by Task T040a:

```bash
python code/analysis/task040a_sweep_hygiene.py
```

This script will:
- Generate matrices for the defined grid: N ranges, theta values [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], and seeds [42, 123, 456, 789]
- Save matrices to `data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy`
- Compute SHA-256 checksums and write to `state/checksums_sweep.json`

### Step 2: Run the Parameter Sweep Orchestrator

Execute the sweep orchestrator (Task T020a) to process the raw data and run simulations:

```bash
python code/analysis/threshold_sweep.py
```

This will:
- Ingest checksummed raw data
- Execute the simulation loop (adding perturbations, computing eigenvalues)
- Produce `data/processed/mc_results.csv` and `data/processed/convergence_data.json`

### Step 3: Validate Sweep Results

Apply the strict outlier validation logic (Task T020b):

```bash
python code/analysis/validate_sweep_results.py
```

This produces `data/processed/validated_sweep_results.csv` with data points meeting the 1e-10 tolerance.

### Step 4: Identify Critical Threshold

Run the threshold identification analysis (Task T021c):

```bash
python code/analysis/threshold_identification.py
```

This performs logistic regression to estimate $\theta_c$ and outputs `data/processed/threshold_identification.json`.

### Step 5: Generate Critical Threshold Report

Extract the final results (Task T023):

```bash
python code/analysis/critical_threshold_report.py
```

This writes `data/processed/critical_threshold_report.json` with the fitted $\theta_c$ and confidence intervals.

### Step 6: Visualize Results

Generate the outlier probability plot (Task T025):

```bash
python code/analysis/plot_outlier_probability.py
```

Output: `data/figures/outlier_probability_vs_theta.png`

## Reproducing the Sensitivity Analysis

The sensitivity analysis (User Story 3) examines the robustness of findings to sparsity parameter choices.

### Step 1: Run Sensitivity Density Sweep

Execute the sensitivity analysis runner (Task T028):

```bash
python code/analysis/sensitivity_density_sweep.py
```

This sweeps support density $\{0.2, 0.3\}$ for each perturbation type (diagonal, block-sparse, random sparse) across multiple seeds, outputting `data/processed/sensitivity_density_sweep.csv`.

### Step 2: Record Sensitivity Metadata

Record perturbation configurations (Task T028b):

```bash
python code/analysis/sensitivity_metadata_recorder.py
```

Output: `data/processed/sensitivity_metadata.json`

### Step 3: Compute Sensitivity Variation

Calculate threshold variation and statistical validation (Task T029a):

```bash
python code/analysis/sensitivity_variation.py
```

Output: `data/processed/sensitivity_variation.csv` with p-values and shift flags.

### Step 4: Generate Sensitivity Report

Produce the final sensitivity report (Task T030):

```bash
python code/analysis/generate_sensitivity_report.py
```

Output: `data/processed/sensitivity_report.md`

## Verification

To verify the full pipeline:

1. Check that all expected output files exist:
 - `data/processed/mc_results.csv`
 - `data/processed/validated_sweep_results.csv`
 - `data/processed/threshold_identification.json`
 - `data/processed/critical_threshold_report.json`
 - `data/processed/sensitivity_density_sweep.csv`
 - `data/processed/sensitivity_variation.csv`
 - `data/processed/sensitivity_report.md`
 - `data/figures/outlier_probability_vs_theta.png`

2. Verify checksums:
 ```bash
 python code/analysis/sweep_checksums.py
 ```

3. Run unit tests:
 ```bash
 cd code
 python -m pytest tests/unit/ -v
 ```

## Notes

- All matrix operations use CPU-tractable iterative solvers (ARPACK) to fit within memory constraints.
- The "observer" in this study is the deterministic computational algorithm measuring spectral statistics, as clarified in `research.md` (Task T033).
- Results are framed as purely observational correlations with no physical "observer" modeling beyond computational measurement.
- Ensure sufficient disk space for raw matrix data (depends on grid size).