# Quickstart Guide

## Prerequisites
- Python 3.9+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Run the Analysis Pipeline

1. **Generate Hamiltonians and Eigenstates** (Phase 2 & 3)
 ```bash
 python code/main.py
 ```
 This will generate disorder realizations, compute eigenstates, and log residuals.

2. **Compute Participation Ratio and Scaling** (Phase 3)
 ```bash
 python code/analyze_pr.py
 ```
 This computes PR for eigenstates and performs finite-size scaling.
 Output: `data/processed/scaling_fits.json`, `data/processed/pr_scaling_plot.png`

3. **Apply Bonferroni Correction** (Phase 3, Task T015)
 ```bash
 python code/apply_bonferroni.py
 ```
 This reads `scaling_fits.json`, applies Bonferroni correction, and writes results.
 Output: `data/processed/bonferroni_results.json`

4. **Compute Transfer Matrix Method** (Phase 4)
 ```bash
 python code/analyze_tm.py
 ```
 Output: `data/processed/lyapunov_exponents.json`, `data/metadata/tm_convergence.json`

5. **Compare Methods** (Phase 4.5)
 ```bash
 python code/compare_methods.py
 ```
 Output: `data/processed/method_agreement_report.json`

6. **Visualize Eigenstates** (Phase 5)
 ```bash
 python code/visualize.py
 ```
 Output: `data/processed/visualizations/*.png`, `docs/physical_interpretation.md`

7. **Log Residuals** (Constitution Principle VI)
 The `code/main.py` and `code/analyze_pr.py` scripts already invoke `residual_logger` internally.
 To ensure the residuals file is created and populated, run:
 ```bash
 python code/residual_logger.py
 ```
 Output: `data/metadata/residuals.json`

## Expected Outputs
- `data/processed/scaling_fits.json`
- `data/processed/bonferroni_results.json`
- `data/processed/lyapunov_exponents.json`
- `data/processed/method_agreement_report.json`
- `data/metadata/residuals.json`
- `data/processed/visualizations/`
- `docs/physical_interpretation.md`

## Validation
Run the validation script to check all outputs:
```bash
python code/validate_outputs.py
```