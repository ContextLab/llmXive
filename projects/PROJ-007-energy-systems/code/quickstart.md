# Quickstart Guide: Energy Systems Causal Pipeline

This guide provides the exact commands to run the full causal inference pipeline for analyzing energy inequity in low-income communities. The pipeline ingests public microdata (EIA RECS and ACS), performs Propensity Score Matching (PSM), validates covariate balance, estimates causal effects, and generates a comprehensive report.

## Prerequisites

- Python 3.9+
- Installed dependencies: `pip install -r requirements.txt`

## Running the Pipeline

Execute the main pipeline script with the configuration file:

```bash
python code/src/main.py --config code/src/config.yaml
```

This command performs the following steps:
1. **Data Ingestion**: Fetches EIA RECS and ACS data.
2. **Preprocessing**: Filters for low-income households, constructs treatment variables, and handles missing values.
3. **Propensity Score Matching**: Estimates propensity scores and matches treated/control pairs.
4. **Balance Validation**: Checks Standardized Mean Differences (SMD) and runs placebo tests.
5. **Causal Estimation**: Runs OLS regression with cluster-robust standard errors.
6. **Sensitivity Analysis**: Sweeps caliper values to test robustness.
7. **Output Generation**: Saves results to `data/outputs/analysis_result.json`.

## Expected Output

Upon successful execution, the pipeline generates `data/outputs/analysis_result.json`.

### JSON Structure

The output file contains the following structure:

```json
{
 "metadata": {
 "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
 "config_path": "src/config.yaml",
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
 ],
 "graceful_degradation_status": {
 "halt_reason": null,
 "methodology_attempted": "PSM + OLS",
 "data_availability_check": "PASSED"
 }
}
```

### Graceful Degradation

If PSM balance fails and longitudinal data is missing (making DiD impossible), the pipeline halts with a `DataUnavailableError`. The `graceful_degradation_status` field will populate with:
- `halt_reason`: "Causal Identification Failure: PSM Balance Not Achieved and DiD Fallback Impossible"
- `methodology_attempted`: "PSM (Failed)"
- `data_availability_check`: "FAILED"

## Validation

To verify the JSON output structure:

```bash
python -m json.tool data/outputs/analysis_result.json
```

## Troubleshooting

- **Import Errors**: Ensure `src/utils/logging.py` contains `get_logger` and `set_seed`.
- **Schema Errors**: Ensure `src/models/schemas.py` includes `GracefulDegradationStatus`.
- **Data Fetch Failures**: The pipeline requires real data from EIA RECS and ACS. If these sources are unreachable, the pipeline will halt with a clear error message. Do not use synthetic data.