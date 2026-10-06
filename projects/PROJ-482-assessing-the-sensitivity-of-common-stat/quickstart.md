# Quickstart Guide: Assessing the Sensitivity of Common Statistical Tests

This guide outlines the steps to run the full simulation pipeline, from data generation to stability analysis.

## 1. Environment Setup

Ensure you have Python 3.11+ and the required dependencies installed:

```bash
pip install -r requirements.txt
```

## 2. Data Generation

Generate the initial synthetic datasets for validation and simulation.

```bash
python code/run_data_gen.py --config code/config.yaml
```

This produces `data/raw/sample_validation.csv` for manual verification.

## 3. Simulation Execution

Run the full Monte Carlo simulation batch. This executes the adaptive loop for t-tests, ANOVA, and Chi-squared tests.

```bash
python code/run_simulation.py --config code/config.yaml
```

This produces:
- `data/processed/raw_pvalues.csv`
- `data/processed/outcomes.csv`
- `data/processed/aggregated_results.csv`

## 4. Analysis & Visualization

### 4.1 Aggregate Results & Bootstrap CIs (T026/T026b)
(Handled internally by `run_simulation.py` or via `run_analyzer.py` if separated)

### 4.2 Stability Analysis (T026c)
Perform trend analysis to verify SC-002 (slope < 0.01).

```bash
python code/run_stability_analysis.py --input data/processed/aggregated_results.csv --output data/processed/
```

This produces:
- `data/processed/stability_trend.csv`
- `data/processed/plots/stability_trend.png`
- `data/processed/stability_report.json`

## 5. Validation

Run the validation script to ensure all deliverables are present.

```bash
python code/validate_quickstart.py
```

## 6. Interpretation

- **Stability**: Check `stability_report.json` for the `success` flag. If `true`, the Type I error rate is stable across sample sizes.
- **Power**: Compare observed power curves (from `power_curve_validation.csv`) with theoretical curves.
- **Regression**: Review `regression_results.json` for the Cox-Snell R² and coefficient significance.
