# Quickstart Guide: Energy Systems Causal Pipeline

This guide details how to run the full causal inference pipeline to analyze energy inequity in low-income communities using EIA RECS and ACS data.

## Prerequisites

1. **Python Environment**: Ensure you are using Python 3.9+.
2. **Dependencies**: Install all required packages:
 ```bash
 pip install -r requirements.txt
 ```
3. **Data Access**: The pipeline will attempt to download real data from the EIA RECS and US Census APIs. Ensure your environment has internet access.
 * **Note**: If data download fails due to API restrictions, the pipeline will halt with a clear error message. Do not use synthetic data.

## Running the Full Pipeline

The main entry point for the causal analysis is `src/main.py`. It orchestrates the following steps:
1. **Ingestion**: Fetches EIA RECS and ACS data.
2. **Preprocessing**: Filters for low-income households, handles missing values, and constructs treatment variables.
3. **Propensity Score Matching (PSM)**: Matches treated and control groups to ensure covariate balance.
4. **Causal Estimation**: Calculates the Average Treatment Effect on the Treated (ATT) using OLS.
5. **Sensitivity Analysis**: Sweeps caliper values to test robustness.
6. **Output**: Generates a JSON report.

Execute the pipeline with the default configuration:

```bash
python code/src/main.py --config code/src/config.yaml
```

### Expected Behavior

* **Success**: The script completes without error, writing the results to `code/data/outputs/analysis_result.json`.
* **Graceful Degradation**: If PSM balance is not achieved (SMD > 0.1) and longitudinal data is missing (making DiD impossible), the pipeline will halt with a `DataUnavailableError` and a clear log message: "Causal Identification Failure: PSM Balance Not Achieved and DiD Fallback Impossible (Cross-Sectional Data). Pipeline Halted."

## Output Format

Upon successful completion, the pipeline generates `code/data/outputs/analysis_result.json`. This file contains the full analysis results, including metadata, data summaries, balance metrics, causal estimates, and sensitivity analysis.

### JSON Structure

The output JSON follows this schema:

```json
{
 "metadata": {
 "timestamp": "ISO-8601-timestamp",
 "config_path": "path/to/config.yaml",
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
 },
...
 ]
}
```

### Field Descriptions

* **metadata**: Execution context information.
* **data_summary**: Counts of households processed and matched pairs formed.
* **balance_results**: Metrics verifying the quality of the PSM match. `max_smd` should be <= 0.1.
* **causal_estimation**: The primary result. `att_estimate` represents the estimated reduction in energy cost burden due to solar/microgrid adoption.
* **sensitivity_analysis**: A list of results from running the analysis with different caliper values to assess robustness.

## Validation

To verify the output is valid JSON, run:

```bash
python -m json.tool code/data/outputs/analysis_result.json > /dev/null
```

If the command exits with code 0, the output structure is valid.