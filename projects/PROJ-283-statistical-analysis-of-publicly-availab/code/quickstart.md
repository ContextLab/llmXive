# Quickstart Guide for Statistical Analysis of Chess Elo Data

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Run the Pipeline
The pipeline consists of several steps. Run them in order:

1. **Download Data** (Optional if data exists):
 ```bash
 python code/src/data/download.py
 ```

2. **Parse and Process Data**:
 ```bash
 python code/src/main.py
 ```
 *Note: This orchestrates parsing, processing, and initial validation.*

3. **Fit Models and Save Metrics (T027)**:
 ```bash
 python code/src/models/fit.py
 ```
 This step fits Beta and Ridge regression models and saves results to `data/results/model_metrics.json`.

4. **Validate Contracts** (Optional):
 ```bash
 python code/src/validation/validate_contracts.py --data data/processed/games.parquet --contracts specs/contracts/game_record.schema.yaml
 ```

## Expected Outputs
- `data/processed/games.parquet`: Processed game records.
- `data/results/model_metrics.json`: Model coefficients, p-values, R², AIC.
- `data/results/diagnostics.json`: Diagnostic report.
- `data/results/*.png`: Diagnostic plots.
