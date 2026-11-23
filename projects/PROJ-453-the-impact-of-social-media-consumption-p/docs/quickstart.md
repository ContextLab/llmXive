# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r code/requirements.txt
```

## Execution Pipeline
Run the following commands in order to execute the full analysis:

1. **Setup Directories**:
 ```bash
 python code/setup_directories.py
 ```

2. **Feasibility Check**:
 ```bash
 python code/00_feasibility_check.py
 ```

3. **Data Ingestion**:
 ```bash
 python code/01_ingest.py
 ```

4. **Variable Engineering**:
 ```bash
 python code/02_engineer.py
 ```

5. **Model Fitting**:
 ```bash
 python code/03_model.py
 ```

6. **Visualization**:
 ```bash
 python code/04_visualize.py
 ```

## Output
- `data/processed/participants_cleaned.csv`: Cleaned dataset
- `results/models/regression_summary.json`: Model results
- `results/figures/`: Generated plots
