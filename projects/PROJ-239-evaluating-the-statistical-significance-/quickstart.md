# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running Tests
Run the full test suite:
```bash
pytest tests/
```

Expected output: All tests pass (exit code 0).

## Running Simulations

### Baseline Simulation (Naive T-Test)
```bash
python code/run_simulation_baseline.py --icc 0.1 --iterations 100 --seed 42
```
Output: `data/derived/baseline_results.csv`

### Robust Simulation (Cluster-Robust & Permutation)
```bash
python code/run_simulation_robust.py --icc 0.1 --iterations 100 --seed 42
```
Output: `data/derived/robust_results.csv`

## Generating Final Report
```bash
python code/generate_final_report.py
```
Output: `specs/001-evaluating-the-statistical-significance/research.md`

## Validation
The project passes validation when:
- `pytest tests/` exits with code 0
- All simulation scripts produce valid CSV outputs
- Final report is generated with all required sections

Note: This guide has been updated to reflect the completed test suite and simulation workflows.