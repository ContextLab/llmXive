# Quickstart Guide: PROJ-786 Multi-Property Trade-Offs

This guide validates the end-to-end execution of the research pipeline.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. (Optional) Create `.env` file if you need to override defaults.

## Execution Steps

Run the following commands in order to execute the full pipeline:

1. **Data Ingestion** (Fetches OQMD data):
 ```bash
 python code/data_ingestion.py
 ```

2. **Feature Encoding** (Encodes compositions):
 ```bash
 python code/feature_encoder.py
 ```

3. **Model Training & Validation** (Trains models, runs LOSO-CV):
 ```bash
 python code/model_training.py
 ```

4. **Pareto Optimization** (Generates frontier):
 ```bash
 python code/pareto_optimization.py
 ```

5. **Cluster & Sensitivity Analysis** (Identifies decoupled regions):
 ```bash
 python code/cluster_analysis.py
 ```

6. **Metrics Calculation** (Calculates dominance metrics):
 ```bash
 python code/metrics_calculation.py
 ```

7. **Robustness Validation** (Validates SC-003 compliance):
 ```bash
 python code/robustness_validation.py
 ```

## Expected Outputs

Ensure the following files exist after running the steps:

- `data/processed/encoded_alloys.csv`
- `data/processed/model_validation_report.json`
- `data/processed/sensitivity_analysis.csv`
- `data/results/robustness_validation.json`
- `data/results/decoupling_plot.png`
- `data/processed/loso_test_points.csv`
- `data/processed/theoretical_bounds.json`