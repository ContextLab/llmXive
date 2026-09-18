# Quick Start Guide: Energy Systems Causal Pipeline

This guide details how to run the full causal inference pipeline to analyze energy inequity in low-income communities using EIA RECS and ACS data.

## Prerequisites

Ensure you have installed the project dependencies:

```bash
pip install -r requirements.txt
```

## Running the Full Pipeline

To execute the complete pipeline (Data Ingestion -> Preprocessing -> Propensity Score Matching -> Causal Estimation -> Sensitivity Analysis -> Report Generation), run the following command from the project root:

```bash
python code/src/main.py --config code/src/config.yaml
```

### Command Arguments

- `--config`: Path to the YAML configuration file defining seeds, paths, and thresholds. Defaults to `code/src/config.yaml`.

## Expected Execution Flow

1. **Ingestion**: The system fetches EIA RECS and ACS data. If required columns (income, energy_cost, solar_installation, location) are missing, the pipeline halts.
2. **Preprocessing**: Low-income households are filtered, treatment variables are constructed, and missing values are imputed.
 - *Power Check*: If fewer than 50 adopters remain, a `PowerError` is raised.
3. **PSM & Balance**: Propensity scores are estimated, and nearest-neighbor matching is performed.
 - *Balance Check*: If the maximum Standardized Mean Difference (SMD) exceeds 0.1, or the placebo test fails, the pipeline triggers the **Graceful Degradation Protocol**.
4. **Causal Estimation**:
 - If balance passes: OLS regression with cluster-robust standard errors is run.
 - If balance fails: The system checks for longitudinal data. Since EIA RECS/ACS is cross-sectional, `DataUnavailableError` is raised, and the pipeline halts with a clear message: "Causal Identification Failure: PSM Balance Not Achieved and DiD Fallback Impossible (Cross-Sectional Data)."
5. **Sensitivity Analysis**: A caliper sweep is performed to test the robustness of the ATT estimate.
6. **Output**: Results are serialized to JSON.

## Output Artifacts

Upon successful completion, the pipeline generates the following file:

- `code/data/outputs/analysis_result.json`: Contains the full analysis results, including metadata, data summaries, balance metrics, causal estimates, and sensitivity data.

## Expected JSON Structure

The output file `data/outputs/analysis_result.json` follows this structure:

```json
{
 "metadata": {
 "timestamp": "ISO-8601-timestamp",
 "config_path": "code/src/config.yaml",
 "pipeline_version": "1.0.0"
 },
 "data_summary": {
 "total_households": 12345,
 "treated_count": 456,
 "control_count": 11889,
 "matched_pairs": 400
 },
 "balance_results": {
 "max_smd": 0.08,
 "caliper_used": 0.05,
 "balance_status": "PASS",
 "placebo_p_value": 0.45
 },
 "causal_estimation": {
 "methodology": "OLS",
 "att_estimate": -150.23,
 "att_std_error": 45.12,
 "p_value": 0.001,
 "confidence_interval_95": [-238.66, -61.80],
 "n_observations": 856
 },
 "sensitivity_analysis": [
 {
 "caliper": 0.01,
 "att_estimate": -148.50,
 "p_value": 0.002
 },
 {
 "caliper": 0.05,
 "att_estimate": -150.23,
 "p_value": 0.001
 },
 {
 "caliper": 0.10,
 "att_estimate": -152.10,
 "p_value": 0.001
 }
 ]
}
```

### Field Descriptions

- `metadata`: Execution context and versioning.
- `data_summary`: Counts of households, treated units, control units, and matched pairs.
- `balance_results`: Metrics validating the quality of the matching process (SMD, caliper, placebo p-value).
- `causal_estimation`: The primary result. Includes the Average Treatment Effect on the Treated (ATT), standard error, p-value, and 95% confidence interval.
- `sensitivity_analysis`: A list of results from the caliper sweep, showing how the ATT estimate varies with different matching strictness levels.

## Validation

To verify the JSON output is valid:

```bash
python -m json.tool code/data/outputs/analysis_result.json
```

## Troubleshooting

- **Import Errors**: Ensure `code/` is in your `PYTHONPATH` or run from the project root.
- **Data Fetching Failures**: The pipeline will fail loudly if the EIA or ACS APIs are unreachable or return unexpected schemas. Check the logs for specific column errors.
- **Balance Failure**: If the pipeline halts with "Causal Identification Failure," it indicates that PSM could not achieve balance and the DiD fallback is impossible due to the cross-sectional nature of the data. This is the expected behavior per the Graceful Degradation Protocol.
