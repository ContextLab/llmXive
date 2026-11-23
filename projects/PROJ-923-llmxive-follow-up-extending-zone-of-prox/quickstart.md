# Quickstart Guide

## Prerequisites
- Python 3.9+
- pip

## Setup
1. Clone the project repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline
1. **Run a single baseline simulation**:
 ```bash
 python code/main.py --mode baseline --seed 42
 ```
 This will generate a convergence curve in `data/metrics/baseline_results.csv`.

2. **Run a single CAP simulation**:
 ```bash
 python code/main.py --mode cap --seed 42
 ```
 This will generate a convergence curve in `data/metrics/cap_results.csv`.

3. **Run the full batch experiment**:
 ```bash
 python code/main.py --runs 100 --tasks 10
 ```
 This will generate 100 runs (10 tasks x 10 seeds) and output `data/metrics/batch_results.csv`.

4. **Generate comparative report**:
 After batch runs are complete, the report is automatically generated in `figures/comparison_report.png`.

## Testing
Run all tests:
```bash
pytest tests/ -v
```

## Validation
Validate results against schema:
```bash
python code/analysis/validate_results.py
```
