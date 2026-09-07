# Quickstart Guide: Energy Inequity Causal Analysis Pipeline

This guide explains how to run the full causal inference pipeline to analyze energy inequity in low-income communities using EIA RECS and ACS data.

## Prerequisites

- Python 3.9+
- `pip install -r requirements.txt`

## Running the Pipeline

Execute the main pipeline script with the configuration file:

```bash
python code/src/main.py --config code/src/config.yaml
```

This command will:
1. Ingest EIA RECS and ACS data
2. Filter for low-income households and construct treatment variables
3. Perform Propensity Score Matching (PSM) with balance validation
4. Estimate causal effects (ATT) using OLS or DiD fallback
5. Run sensitivity analysis across caliper values
6. Generate the final analysis report

## Expected Output

Upon successful completion, the pipeline produces:
- `data/outputs/analysis_result.json`: Contains the ATT estimate, p-values, confidence intervals, methodology details, and sensitivity analysis data.

### Verifying Output Integrity

Verify the JSON output is valid:

```bash
python -m json.tool data/outputs/analysis_result.json > /dev/null && echo "JSON is valid"
```

### Expected JSON Structure

The `analysis_result.json` file will contain:
```json
{
 "att_estimate": <float>,
 "p_value": <float>,
 "confidence_interval": [<float>, <float>],
 "methodology": "OLS" | "DiD",
 "balance_status": "PASS" | "FAIL",
 "sensitivity_analysis": [
 {"caliper": <float>, "att": <float>, "p_value": <float>},
...
 ],
 "timestamp": "<ISO8601 timestamp>"
}
```

## Troubleshooting

- **Missing Data**: Ensure `data/raw/` contains the necessary EIA RECS and ACS files, or that the ingest script can reach the real data sources.
- **Power Error**: If fewer than 50 adopters remain after filtering, the pipeline will halt with a `PowerError`.
- **Balance Failure**: If PSM fails to achieve balance (SMD > 0.1) and longitudinal data is missing, the pipeline will halt with a `BalanceFailureError`.
