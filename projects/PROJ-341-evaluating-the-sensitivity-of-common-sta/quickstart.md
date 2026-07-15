# Quickstart Guide

This guide explains how to set up and run the simulation pipeline for evaluating the sensitivity of common statistical tests to dataset size.

## Prerequisites

- Python 3.10+
- pip

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Structure

The project uses the following structure:
- `code/`: Source code
- `data/`: Data files (raw, simulation, visualization, reports)
- `tests/`: Unit and integration tests

## Running the Pipeline

### 1. Initialize Directories and Metadata

Ensure the directory structure and metadata file are created:
```bash
python code/setup_directories.py
python code/utils/metadata_manager.py --init
```

### 2. Run Tests (Optional)

Run the unit tests to ensure everything is working:
```bash
python code/run_tests.py
```

### 3. Run the Simulation

Run the full simulation with default parameters:
```bash
python code/main.py
```

Or with custom parameters:
```bash
python code/main.py --test t-test --min-n 5 --max-n 50 --step-n 5 --effect-sizes 0.2,0.5,0.8 --hypotheses null_true,alt_true --iterations 1000
```

### 4. Run Validation (Optional)

Run the validation against real-world datasets:
```bash
python code/main.py --mode validation
```

## Output Files

The pipeline generates the following output files:
- `data/simulation/p_values_raw.csv`: Raw p-values from the simulation.
- `data/simulation/error_rates_summary.csv`: Aggregated error rates.
- `data/simulation/thresholds.json`: Identified reliability thresholds.
- `data/simulation/validation_metrics.json`: Validation metrics and KS statistics.
- `data/simulation/real_data_pvalues.csv`: P-values from real-world datasets.
- `data/simulation/real_data_power.json`: Bootstrapped power estimates.
- `data/simulation_metadata.json`: Metadata for all runs, seeds, and configurations.
- `data/reports/validation_report.md`: Validation report.
- `data/visualization/`: Generated plots.

## Troubleshooting

- **Memory Issues**: The simulation is designed to run within 7GB RAM. If you encounter memory issues, reduce the number of iterations or use a smaller sample size range.
- **Missing Files**: Ensure that `data/simulation_metadata.json` exists. Run `python code/utils/metadata_manager.py --init` to create it.
- **Import Errors**: Make sure all dependencies are installed via `pip install -r requirements.txt`.