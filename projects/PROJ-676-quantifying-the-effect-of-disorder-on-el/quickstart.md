# Quickstart Guide: Quantifying the Effect of Disorder on Electronic Transport

This guide ensures the end-to-end reproducibility of the research pipeline.

## Prerequisites

- Python 3.9+
- `pip install -r requirements.txt`

## Execution Steps

1. **Setup Project Structure** (Run once)
 ```bash
 python code/setup_project_structure.py
 ```

2. **Generate Hamiltonians** (Data Generation)
 ```bash
 python code/generate_hamiltonian.py
 ```
 *Outputs: `data/raw/hamiltonians.h5`, `data/metadata/provenance.json`*

3. **Analyze Participation Ratio (US1)**
 ```bash
 python code/analyze_pr.py
 ```
 *Outputs: `data/processed/scaling_fits.json`, `data/processed/pr_scaling_plot.png`, `data/metadata/residuals.json`*

4. **Aggregate Results & Apply Bonferroni (T013b/T015)**
 ```bash
 python code/aggregate_and_correct_stats.py
 ```
 *Outputs: `data/processed/bonferroni_results.json` (validates T013b completion)*

5. **Transfer Matrix Validation (US2)**
 ```bash
 python code/analyze_tm.py
 ```
 *Outputs: `data/processed/lyapunov_exponents.json`, `data/metadata/tm_convergence.json`*

6. **Visualize Eigenstates (US3)**
 ```bash
 python code/visualize.py
 ```
 *Outputs: `data/processed/visualizations/*.png`, `docs/physical_interpretation.md`*

## Verification

Run the following to check for required artifacts:
```bash
ls -l data/processed/scaling_fits.json
ls -l data/processed/bonferroni_results.json
ls -l data/metadata/residuals.json
```
