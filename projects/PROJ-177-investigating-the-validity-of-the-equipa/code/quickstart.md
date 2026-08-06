# Quickstart Guide: Investigating the Validity of the Equipartition Theorem

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Quick Run

Execute the full pipeline with a 10% sample of the data:

```bash
python code/main.py --stage all --sample-ratio 0.1
```

Or run individual stages:

```bash
# Ingest and compute energies
python code/main.py --stage ingest --sample-ratio 0.1

# Statistical analysis
python code/main.py --stage stats --alpha 0.01

# Sensitivity analysis
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10

# Regression analysis
python code/main.py --stage regression
```

## Output Artifacts

- `data/derived/energy_samples.csv`: Computed energy components
- `artifacts/statistical_results.json`: KS/Chi-squared test results
- `artifacts/sensitivity_analysis_report.json`: Threshold sensitivity
- `artifacts/regression_results.json`: Regression analysis

## Verification

Ensure all artifacts are generated and checksums match:

```bash
python code/hash_artifacts.py
```
