# Quickstart Guide: Statistical Test Sensitivity Simulation

## Prerequisites
- Python 3.8+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Running the Full Simulation (User Story 1)
This command runs the parameter loop for n=5 to n=500 (step 5), across effect sizes 0.2, 0.5, 0.8, for 10,000 iterations per condition.

**Note**: This is a long-running process. For testing, reduce `--max-n` and `--iterations`.

```bash
# Full run (may take hours):
python code/main.py --test t-test --min-n 5 --max-n 500 --step-n 5 --effect-size 0.2,0.5,0.8 --hypothesis H1 --iterations 10000 --alpha 0.05 --seed 42

# Quick test run (fast, limited scope):
python code/main.py --test t-test --min-n 5 --max-n 50 --step-n 5 --effect-size 0.2 --hypothesis H1 --iterations 1000 --alpha 0.05 --seed 42
```

**Output**:
- `data/simulation/p_values_raw.csv` (Raw p-values from all iterations)

## Running Aggregation (User Story 1 - Post-processing)
```bash
python code/analysis/aggregator.py
```
**Output**:
- `data/simulation/error_rates_summary.csv`

## Running Threshold Analysis (User Story 2)
```bash
python code/analysis/threshold_finder.py
```
**Output**:
- `data/simulation/thresholds.json`

## Running Visualization (User Story 2)
```bash
python code/visualization/plotter.py
```
**Output**:
- `data/visualization/*.png`

## Running Validation (User Story 3)
```bash
python code/main.py --mode validation
```
**Output**:
- `data/simulation/real_data_pvalues.csv`
- `data/simulation/real_data_power.json`
- `data/simulation/validation_metrics.json`
- `data/reports/validation_report.md`

## Running Tests
```bash
python code/run_tests.py
```