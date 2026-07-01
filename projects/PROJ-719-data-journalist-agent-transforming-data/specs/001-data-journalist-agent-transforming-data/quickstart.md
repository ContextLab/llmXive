# Quickstart: Data2Story Completeness Audit Adaptation

This script reproduces the **Completeness Gates** verification logic from the Data Journalist Agent paper. It simulates the "Find-Data" and "Inspector" agents by generating synthetic datasets, running the deterministic audit rules, and producing verification artifacts.

## Prerequisites
Ensure you have the required lightweight dependencies:
```bash
pip install pandas numpy matplotlib
```

## Run the Adaptation
Execute the following command to run the full simulation:

```bash
python code/run_adaptation.py
```

## Expected Outputs
After execution, the following artifacts will be generated:

1.  **`data/audit_report.json`**: A JSON file containing the aggregated results of the audit, including the pass/fail rate of the simulated datasets against the paper's defined gates (Row count, Non-null rate, Year span).
2.  **`data/audit_X.json`**: Individual audit reports for each simulated dataset.
3.  **`figures/quality_distribution.png`**: A visualization comparing the row counts and non-null rates of the datasets against the required thresholds.

## Verification
You can verify the results by inspecting the JSON:
```bash
cat data/audit_report.json
```
The `gate_success_rate` should reflect the proportion of synthetic datasets that met all criteria (e.g., >50 rows, >50% non-null values).
