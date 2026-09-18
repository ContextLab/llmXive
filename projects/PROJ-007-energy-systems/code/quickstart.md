# Quick Start Guide: Energy Systems Causal Analysis Pipeline

This guide provides exact commands to run the full causal inference pipeline for analyzing energy inequity in low-income communities. The pipeline ingests real public data (EIA RECS and ACS), performs propensity score matching, estimates causal effects, and generates a comprehensive report.

## Prerequisites

Ensure you have Python 3.9+ installed and the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Full Pipeline

Execute the main pipeline script with the configuration file:

```bash
python code/src/main.py --config code/src/config.yaml
```

This single command performs the following steps in sequence:

1. **Data Ingestion**: Fetches EIA RECS and ACS data from official sources.
2. **Preprocessing**: Filters for low-income households, handles missing values, winsorizes outliers, and constructs treatment variables.
3. **Propensity Score Matching**: Estimates propensity scores, matches treated and control units, and validates covariate balance (SMD <= 0.1).
4. **Causal Estimation**: Runs OLS regression with cluster-robust standard errors to estimate the Average Treatment Effect on the Treated (ATT).
5. **Sensitivity Analysis**: Sweeps caliper values to assess robustness of the ATT estimate.
6. **Result Serialization**: Saves the final analysis results to `data/outputs/analysis_result.json`.

## Expected Output

Upon successful completion, the pipeline generates `data/outputs/analysis_result.json` containing the following structure:

```json
{
 "metadata": {
 "timestamp": "ISO-8601-timestamp",
 "config_path": "code/src/config.yaml",
 "pipeline_version": "1.0.0"
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
 "balance_status": "PASS",
 "placebo_p_value": <float>
 },
 "causal_estimation": {
 "methodology": "OLS",
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

### Field Descriptions

- **metadata**: Timestamp of the run, config file path, and pipeline version.
- **data_summary**: Counts of total households, treated units, control units, and matched pairs.
- **balance_results**: Maximum Standardized Mean Difference (SMD), caliper value used, balance status ("PASS" or "FAIL"), and placebo test p-value.
- **causal_estimation**: Methodology used (e.g., "OLS"), ATT estimate, standard error, p-value, 95% confidence interval, and number of observations.
- **sensitivity_analysis**: Array of sensitivity analysis results for different caliper values, including ATT estimate and p-value.

## Graceful Degradation Protocol

If PSM balance fails and longitudinal data is missing (which is the case for cross-sectional EIA RECS/ACS data), the pipeline will halt with a clear error message:

```
Causal Identification Failure: PSM Balance Not Achieved and DiD Fallback Impossible (Cross-Sectional Data). Pipeline Halted.
```

This behavior adheres to the 'Graceful Degradation Protocol' mandated by the project plan, ensuring that invalid causal estimates are not produced.

## Validation

To verify the JSON output structure, run:

```bash
python -m json.tool code/data/outputs/analysis_result.json
```

## Troubleshooting

- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed.
- **Data Fetch Failures**: The pipeline fetches real data from external sources. Ensure network connectivity and that the specified URLs are accessible.
- **Balance Failure**: If PSM balance fails, the pipeline halts. Check the logs for SMD values and consider adjusting caliper thresholds in `code/src/config.yaml`.
- **Missing Longitudinal Data**: The DiD fallback is impossible with cross-sectional data. The pipeline is designed to halt in this scenario rather than produce invalid results.