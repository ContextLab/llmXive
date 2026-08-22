# Quickstart Guide: Gut Microbiome & Sleep Architecture Pipeline

This guide describes how to run the full analysis pipeline for the project
**PROJ-340-investigating-the-correlation-between-gu**.

## Prerequisites

- Python 3.9+
- `pip` and `venv`
- Required dependencies installed (see `requirements.txt`)

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Ensure `data/config/required_variables.yaml` exists and contains the necessary
predictor and outcome variable names.

## Running the Pipeline

### 1. Generate Synthetic Data (For Testing)

To run the integration test T110 (Synthetic Data Pipeline):

```bash
python code/run_synthetic_pipeline.py
```

This script:
- Generates synthetic metagenomic and sleep data.
- Validates the data against the schema.
- Detects and filters outliers.
- Runs correlation analysis.
- Performs diagnostics (VIF, power, sensitivity).
- Writes all required artifacts to `data/`.

### 2. Run Real Data Pipeline (When Data Available)

```bash
python code/run_real_data_pipeline.py
```

*Note: This will fail if no real data source is configured or available.*

## Verification

After running `run_synthetic_pipeline.py`, verify the following outputs exist:

- `data/raw/synthetic_data.csv`
- `data/results/outlier_report.json`
- `data/processed/filtered_data.parquet`
- `data/results/correlation_matrix.json`
- `data/results/sensitivity_analysis.csv`
- `data/results/timing_evidence.json`

## CI/CD

The pipeline is configured to run in GitHub Actions (`.github/workflows/analysis.yml`).
The CI job executes the synthetic pipeline to verify correctness within the 6-hour limit.

## Troubleshooting

- **Missing Variables**: Ensure `data/config/required_variables.yaml` is populated.
- **Import Errors**: Check that all dependencies are installed.
- **Circular Imports**: Ensure `main.py` and `run_stress_test.py` do not import each other at the module level.
