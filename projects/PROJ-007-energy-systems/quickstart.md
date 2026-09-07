# Quickstart Guide: Energy Systems Causal Inference Pipeline

This guide provides the exact commands to run the full causal inference pipeline
for analyzing energy inequity in low-income communities using EIA RECS and ACS data.

## Prerequisites

- Python 3.9+
- Dependencies installed: `pip install -r requirements.txt`

## Running the Pipeline

Execute the main pipeline script with the configuration file:

```bash
python src/main.py --config src/config.yaml
```

This command will:
1. Ingest EIA RECS and ACS data
2. Filter for low-income households (income < 150% FPL)
3. Construct treatment variables (solar/microgrid adoption)
4. Perform Propensity Score Matching (PSM) with balance validation
5. Estimate causal effects using OLS (or DiD if PSM fails and longitudinal data exists)
6. Run sensitivity analysis across caliper values
7. Generate the final analysis report

## Expected Output

Upon successful completion, the pipeline produces:

### Primary Output File

`data/outputs/analysis_result.json`

This file contains the complete causal inference results in the following JSON structure:

```json
{
 "metadata": {
 "timestamp": "ISO8601 timestamp",
 "config_path": "path to config file",
 "pipeline_version": "version string"
 },
 "data_summary": {
 "total_households": <int>,
 "treated_count": <int>,
 "control_count": <int>,
 "matched_pairs": <int>
 },
 "balance_results": {
 "max_smd": <float>,
 "caliper_used": <float>,
 "balance_status": "PASS" or "FAIL",
 "placebo_p_value": <float>
 },
 "causal_estimation": {
 "methodology": "OLS" or "DiD",
 "att_estimate": <float>,
 "att_std_error": <float>,
 "p_value": <float>,
 "confidence_interval_95": [<float>, <float>],
 "n_observations": <int>
 },
 "sensitivity_analysis": [
 {
 "caliper": <float>,
 "att_estimate": <float>,
 "p_value": <float>
 }
 ]
}
```

### Output Validation

To verify the JSON output is valid:

```bash
python -m json.tool data/outputs/analysis_result.json > /dev/null && echo "JSON is valid"
```

## Troubleshooting

- **PowerError**: If the filtered dataset has fewer than 50 treated households, the pipeline will halt with a `PowerError`.
- **BalanceFailureError**: If PSM cannot achieve SMD <= 0.1 after maximum iterations, the pipeline may fall back to DiD (if longitudinal data exists) or halt.
- **DataUnavailableError**: If DiD is triggered but longitudinal data columns are missing, the pipeline will halt with a clear error message.

## Next Steps

After running the pipeline, review the results in `data/outputs/analysis_result.json`
and generate the final report using:

```bash
python src/reporting/generate_final_report.py --input data/outputs/analysis_result.json --output data/outputs/final_report.md
```
