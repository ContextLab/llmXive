# Quickstart Guide

## Prerequisites

- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`

## Running the Full Pipeline

To run the entire simulation, aggregation, visualization, and validation pipeline:

```bash
python code/main.py --mode full
```

This will:
1. Generate synthetic data and run simulations for t-test, ANOVA, and chi-squared.
2. Aggregate results to calculate Type I and Type II error rates.
3. Identify reliability thresholds.
4. Generate visualizations.
5. Download real-world datasets and validate simulation findings.

## Running Individual Modes

### Simulation Only
```bash
python code/main.py --mode simulation --test t-test --min-n 5 --max-n 50 --iterations 1000
```

### Aggregation Only
```bash
python code/main.py --mode aggregation
```

### Validation Only (Download datasets, run tests, bootstrap power)
```bash
python code/main.py --mode validation
```

## Output Files

- `data/simulation/p_values_raw.csv`: Raw p-values from simulation.
- `data/simulation/error_rates_summary.csv`: Aggregated error rates.
- `data/simulation/thresholds.json`: Identified reliability thresholds.
- `data/visualization/`: Generated plots.
- `data/simulation/real_data_pvalues.csv`: P-values from real datasets.
- `data/simulation/real_data_power.json`: Bootstrapped power and KS distance results.
- `data/simulation/validation_metrics.json`: Overall validation metrics.
- `data/reports/validation_report.md`: Final validation report.

## Testing

Run the test suite:
```bash
python code/run_tests.py
```
or
```bash
pytest tests/
```