# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-239-evaluating-the-statistical-significance-
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Simulation

### Baseline Simulation (Naive T-Test)

Run the baseline simulation with default parameters:
```bash
python code/run_simulation_baseline.py
```

This generates `data/derived/baseline_results.csv`.

### Robust Simulation (Cluster-Aware Methods)

Run the robust simulation with default parameters:
```bash
python code/run_simulation_robust.py
```

This generates `data/derived/robustResults.csv`.

## Generating the Final Report

After running both simulations, generate the final report:
```bash
python code/generate_final_report.py
```

This produces `specs/001-evaluating-the-statistical-significance/research.md` with results, tables, and plots.

## Running Tests

Execute the full test suite:
```bash
pytest tests/
```

To run with verbose output:
```bash
pytest tests/ -v
```

## Configuration

You can customize simulation parameters via CLI arguments:

- `--icc-range`: Comma-separated list of ICC values (e.g., `0.0,0.1,0.2`)
- `--icc-step`: Step size for ICC values (default: 0.1)
- `--alpha-list`: Comma-separated list of significance levels (e.g., `0.01,0.05,0.10`)
- `--iterations`: Number of simulation iterations (default: 1000)
- `--seed`: Random seed for reproducibility (default: 42)

Example:
```bash
python code/run_simulation_robust.py --icc-range 0.0,0.1,0.2 --alpha-list 0.01,0.05 --iterations 500
```

## Data Ingestion (Optional)

To download and validate the UCI Online Retail dataset:
```bash
python code/uci_ingest.py
```

This downloads the dataset to `data/raw/uci_online_retail.csv`, computes a SHA-256 checksum, and scans for PII.

## Troubleshooting

- **Memory Error**: If you encounter memory errors, reduce the number of iterations or observations per cluster.
- **Import Errors**: Ensure all dependencies are installed via `requirements.txt`.
- **Test Failures**: Check that the simulation scripts have been run to generate required data files.