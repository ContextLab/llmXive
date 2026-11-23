# Quickstart Guide: Exploring Network Structure in Superconducting Qubit Coupling

This guide walks you through the execution of the full research pipeline, from data fetching to statistical analysis and validation.

## Prerequisites

1. **IBM Quantum Account**: Ensure you have an active account and a valid API token.
2. **Environment Variable**: Set your IBM Quantum token:
 ```bash
 export IBMQ_TOKEN="your_token_here"
 ```
3. **Dependencies**: Install required packages:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: Ensure `scikit-learn` is installed as it is required for statistical analysis.*

## Execution Steps

Follow these steps in order to generate all research artifacts.

### 1. Fetch Calibration Data

Retrieve the latest calibration data for all accessible backends.
```bash
python code/fetcher.py --save-snapshots
```
*Output: Raw JSON files in `data/raw/`*

### 2. Generate Performance Metrics

Process raw snapshots into a standardized CSV.
```bash
python code/generate_calibration_csv.py
```
*Output: `data/processed/performance_metrics.csv`*

### 3. Compute Graph Metrics

Analyze the topology of qubit coupling maps.
```bash
python code/graph_builder.py --generate-metrics
```
*Output: `data/processed/graph_metrics.csv`*

### 4. Compute Correlations

Perform statistical correlation analysis between topology and performance.
```bash
python code/generate_correlation_results.py
```
*Output: `data/processed/correlation_results.csv`*

### 5. Validate Correlation Results (T054)

Validate the generated correlation results against the defined schema.
```bash
python code/validate_correlation_results_schema.py
```
*Expected Output: "Validation PASSED: All records conform to the schema."*

### 6. Generate Visualizations

Create scatter plots and heatmaps for significant correlations.
```bash
python code/viz.py
```
*Output: Figures in `figures/`*

### 7. Generate Final Report

Compile all results into the final markdown report.
```bash
python code/generate_report.py
```
*Output: `docs/report.md`*

## Verification

To ensure data integrity, run the hygiene script:
```bash
python code/hygiene.py
```

## Troubleshooting

- **Missing Dependencies**: If you encounter `ModuleNotFoundError`, ensure `pip install -r requirements.txt` completed successfully. Specifically check for `scikit-learn`, `pandas`, `networkx`, and `jsonschema`.
- **Invalid Token**: If API calls fail, verify your `IBMQ_TOKEN` environment variable.
- **Empty Data**: If output files are empty, check that the fetcher successfully retrieved data from the IBM Quantum API.