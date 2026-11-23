# Quickstart Guide: Assessing P-Value Validity in High-Dimensional Data

This guide outlines the steps to reproduce the research results.

## Prerequisites

- Python 3.11+
- Dependencies installed (see `requirements.txt`)

## Execution Pipeline

Run the following commands in order to execute the full analysis pipeline.
Ensure you are in the project root directory.

### 1. Initialize and Generate Parameters
```bash
python code/run_power_analysis.py
python code/generate_data.py
```
*Outputs: `data/sweep/params.csv`, `data/sweep/power_analysis_result.json`*

### 2. Generate Seed Map
```bash
python code/generate_seed_map.py
```
*Outputs: `data/sweep/seed_map.json`*

### 3. Run Hypothesis Tests (US2)
```bash
python code/run_tests.py
```
*Outputs: `data/results/pvalues_*.csv`, `data/results/embarrassment_log.csv`*

### 4. Analyze P-Values (US3)
```bash
python code/analyze_pvalues.py
```
*Outputs: `data/results/ks_stats.json`*

### 5. Sensitivity Analysis (T031)
```bash
python code/sensitivity_analysis.py
```
*Outputs: `data/results/sensitivity.csv`*

### 6. Bootstrap Confidence Intervals (T032)
```bash
python code/bootstrap_ci.py
```
*Outputs: `data/results/bootstrap_cis.csv`*

### 7. Generate Documentation
```bash
python code/docs_generator.py
```
*Outputs: `docs/methodology.md`, `docs/results.md`*

## Validation

To verify the pipeline execution:
```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **Missing Input Files**: Ensure previous steps in the pipeline have completed successfully.
- **Memory Errors**: The simulation monitors memory usage; if it exceeds 6GB, it will abort. Reduce the sweep size in `code/generate_data.py` if necessary.
- **High Dimensional Instability**: If `p/n > 10` or the covariance matrix is singular, the process will raise `HighDimensionalInstabilityError`.