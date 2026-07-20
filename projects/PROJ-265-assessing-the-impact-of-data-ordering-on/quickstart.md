# Quickstart: Assessing the Impact of Data Ordering on Bootstrapping

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Simulation
To run the full synthetic simulation (US1 + US2):
```bash
python code/runner.py --full
```

**Note**: This command executes the full batch for phi in [0.0, 0.9] and N in [50, 100, 200] with 1000 trials.
The output will be written to `results/simulation_logs.json` and `results/coverage_metrics.csv`.

## Expected Output
- `results/simulation_logs.json`: Detailed JSON log of all simulation runs.
- `results/coverage_metrics.csv`: Aggregated CSV with coverage metrics and p-values.
- `results/sensitivity_analysis.md`: Generated report on sensitivity to N.
- `results/summary_report.md`: Final summary report.

## Verification
To verify reproducibility:
```bash
python code/runner.py --full --seed 42
pytest tests/test_reproducibility.py::verify_reproducibility
```
