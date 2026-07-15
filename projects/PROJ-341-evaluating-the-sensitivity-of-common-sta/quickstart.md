# Quickstart Guide

This guide explains how to run the full simulation and validation pipeline for the project.

## Prerequisites

- Python 3.8+
- Required packages listed in `requirements.txt`

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Ensure directory structure is created:
 ```bash
 python code/setup_directories.py
 ```

## Running the Pipeline

### Step 1: Run Simulation (User Story 1)

Generates synthetic data and runs statistical tests.

```bash
python code/main.py --mode simulation --min-n 5 --max-n 50 --iterations 1000
```

This will produce:
- `data/simulation/p_values_raw.csv`
- `data/simulation/error_rates_summary.csv`

### Step 2: Threshold Identification (User Story 2)

Analyzes error rates to find reliability thresholds.

```bash
python code/analysis/threshold_finder.py
```

This will produce:
- `data/simulation/thresholds.json`

### Step 3: Visualization (User Story 2)

Generates plots of the results.

```bash
python code/visualization/plotter.py
```

This will produce plots in `data/visualization/`.

### Step 4: Validation (User Story 3)

Downloads real datasets and compares against simulation.

```bash
python code/main.py --mode validation
```

This will produce:
- `data/simulation/real_data_pvalues.csv`

### Step 5: Bootstrapped Power Estimation (Task T032)

Performs bootstrapped power estimation and KS distance validation.

```bash
python code/analysis/bootstrapper.py
```

This will produce:
- `data/simulation/real_data_power.json`

### Step 6: Generate Final Report

```bash
python code/analysis/report_generator.py
```

This will produce:
- `data/reports/validation_report.md`

## Full Pipeline Execution

To run the entire pipeline from scratch:

```bash
# Setup
python code/setup_directories.py

# Simulation
python code/main.py --mode simulation --min-n 5 --max-n 50 --iterations 1000

# Thresholds
python code/analysis/threshold_finder.py

# Visualization
python code/visualization/plotter.py

# Validation
python code/main.py --mode validation

# Bootstrapped Power (T032)
python code/analysis/bootstrapper.py

# Report
python code/analysis/report_generator.py
```

## Testing

Run the test suite:

```bash
python code/run_tests.py
```
