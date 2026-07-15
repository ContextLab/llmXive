# Quickstart Guide: Evaluating Statistical Test Sensitivity

This guide shows how to run the full simulation pipeline and validation.

## Prerequisites

```bash
pip install -r requirements.txt
```

## Directory Structure

- `code/` - Source code
- `data/raw/` - Downloaded real datasets
- `data/simulation/` - Simulation outputs (p-values, error rates, thresholds)
- `data/visualization/` - Generated plots
- `data/reports/` - Generated reports

## Running the Pipeline

### Step 1: Run Full Simulation (User Story 1)

```bash
python code/main.py --mode simulation --iterations 1000
```

This generates synthetic data and runs statistical tests across sample sizes.

### Step 2: Aggregate Results (User Story 1)

```bash
python code/analysis/aggregator.py
```

Computes Type I and Type II error rates from raw p-values.

### Step 3: Find Thresholds (User Story 2)

```bash
python code/analysis/threshold_finder.py
```

Identifies sample size thresholds where error rates deviate from nominal alpha.

### Step 4: Generate Visualizations (User Story 2)

```bash
python code/visualization/plotter.py
```

Creates plots showing error rates vs sample size with confidence intervals.

### Step 5: Run Real Data Validation (User Story 3)

```bash
python code/analysis/validator.py
```

Downloads real datasets (Breast Cancer, Wine, Adult) and runs statistical tests to validate simulation findings.

**Output**: `data/simulation/real_data_pvalues.csv`

### Step 6: Bootstrap Power Analysis (User Story 3)

```bash
python code/analysis/bootstrapper.py
```

Performs bootstrapped power estimation and calculates KS distance.

### Step 7: Generate Validation Report

```bash
python code/analysis/report_generator.py
```

Creates a comprehensive validation report comparing simulated vs real data results.

## Full Pipeline Execution

To run the entire pipeline from scratch:

```bash
# 1. Simulation
python code/main.py --mode simulation --iterations 1000

# 2. Aggregation
python code/analysis/aggregator.py

# 3. Thresholds
python code/analysis/threshold_finder.py

# 4. Plots
python code/visualization/plotter.py

# 5. Validation (Real Data)
python code/analysis/validator.py

# 6. Bootstrap
python code/analysis/bootstrapper.py

# 7. Metrics
python code/analysis/validation_metrics.py

# 8. Report
python code/analysis/report_generator.py
```

## Checking Results

After running the pipeline, check these output files:

- `data/simulation/p_values_raw.csv` - Raw p-values from simulation
- `data/simulation/error_rates_summary.csv` - Aggregated error rates
- `data/simulation/thresholds.json` - Identified reliability thresholds
- `data/simulation/real_data_pvalues.csv` - P-values from real datasets
- `data/simulation/real_data_power.json` - Bootstrapped power estimates
- `data/simulation/validation_metrics.json` - Validation metrics and KS statistics
- `data/visualization/` - Generated plots
- `data/reports/validation_report.md` - Final validation report

## Troubleshooting

### ucimlrepo Import Error

If you see `ImportError: cannot import name 'fetch_dataset' from 'ucimlrepo'`, ensure you have the latest version:

```bash
pip install --upgrade ucimlrepo
```

### Dataset Download Fails

If dataset downloads fail, check your internet connection. The datasets are fetched from UCI via the `ucimlrepo` package.

### Memory Issues

If running out of memory, reduce the number of iterations:

```bash
python code/main.py --mode simulation --iterations 100
```

## Running Tests

```bash
pytest tests/ -v
```