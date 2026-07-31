# Quickstart Guide

This guide describes how to run the full analysis pipeline to reproduce the results.

## Prerequisites

- Python 3.9+
- `pip install -r requirements.txt`

## Execution Order

The pipeline consists of several stages. Run them in the order below to generate all required artifacts.

### 1. Setup Project Structure
```bash
python code/setup_project_structure.py
```

### 2. Generate Hamiltonians and Compute Eigenstates (PR Method)
This step generates disordered Hamiltonians, computes eigenstates, calculates Participation Ratios, performs finite-size scaling, and applies statistical corrections.
```bash
python code/analyze_pr.py
```
**Outputs:**
- `data/processed/scaling_fits.json` (PR scaling results)
- `data/metadata/residuals.json` (Numerical stability logs)
- `data/processed/pr_scaling_plot.png` (Diagnostic plot)

### 3. Apply Bonferroni Correction
This step aggregates the scaling results and applies the Bonferroni correction for the full family of disorder widths.
```bash
python code/apply_bonferroni.py
```
**Outputs:**
- `data/processed/bonferroni_results.json` (Corrected statistical results)

### 4. Transfer Matrix Method (Optional/Parallel)
```bash
python code/analyze_tm.py
```
**Outputs:**
- `data/processed/lyapunov_exponents.json`
- `data/metadata/tm_convergence.json`

### 5. Compare Methods
```bash
python code/compare_methods.py
```
**Outputs:**
- `data/processed/method_agreement_report.json`

### 6. Visualization and Physical Interpretation
```bash
python code/visualize.py
```
**Outputs:**
- `data/processed/visualizations/` (Eigenstate plots)
- `docs/physical_interpretation.md` (Worked examples)

### 7. Run Linting
Ensure code quality before committing.
```bash
bash code/run_linting.sh
```

## Verification

After running the full pipeline, verify the existence of the following key artifacts:
- `data/processed/scaling_fits.json`
- `data/processed/bonferroni_results.json`
- `data/metadata/residuals.json`
- `docs/physical_interpretation.md`
