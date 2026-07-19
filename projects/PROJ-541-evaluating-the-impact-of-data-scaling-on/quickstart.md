# Quickstart Guide

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r code/requirements.txt`

## Running the Pipeline

### 1. Simulation Mode
Run the simulation loop to generate synthetic data and test results.
```bash
python code/main.py --mode simulation --iterations 100
```
This produces `results/simulation_results.csv`.

### 2. Real-World Mode
Ingest real-world datasets and run analysis.
```bash
python code/main.py --mode real_world
```
This requires `data/config/datasets.yaml` to be configured with valid dataset IDs.

### 3. Analysis Mode
Analyze existing simulation results.
```bash
python code/main.py --mode analyze
```

### 4. Visualization Mode
Generate plots from simulation results.
```bash
python code/main.py --mode visualize
```
This produces `figures/error_rate_plot.png`.

### 5. Verification
Verify artifacts.
```bash
python code/verify_artifacts.py
```

## Troubleshooting
- If `datasets` package is missing, install it: `pip install datasets`
- Ensure `data/config/datasets.yaml` exists and contains valid dataset IDs.