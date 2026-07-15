# Quickstart Guide

## Prerequisites

- Python 3.8+
- Required packages listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Running the Full Pipeline

The full pipeline consists of several steps:

### 1. Setup Directories
```bash
python code/setup_directories.py
```

### 2. Download Real Datasets (US3)
```bash
python code/analysis/validator.py
```

### 3. Run Real Data Validation (US3)
```bash
python code/analysis/real_data_runner.py
```

### 4. Run Main Simulation (US1)
```bash
python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000
```

Or run the full simulation grid:
```bash
python code/main.py
```

### 5. Aggregate Results (US1)
```bash
python code/analysis/aggregator.py
```

### 6. Find Thresholds (US2)
```bash
python code/analysis/threshold_finder.py
```

### 7. Generate Visualizations (US2)
```bash
python code/visualization/plotter.py
```

### 8. Run Bootstrapped Power Estimation (US3 - T032)
```bash
python code/analysis/bootstrapper.py
```

### 9. Generate Validation Report (US3)
```bash
python code/analysis/report_generator.py
```

## Expected Outputs

After running the full pipeline, you should see:

- `data/simulation/p_values_raw.csv` - Raw p-values from simulation
- `data/simulation/error_rates_summary.csv` - Aggregated error rates
- `data/simulation/thresholds.json` - Identified thresholds
- `data/simulation/real_data_pvalues.csv` - P-values from real data
- `data/simulation/real_data_power.json` - Bootstrapped power results
- `data/simulation/validation_metrics.json` - Validation metrics
- `data/visualization/*.png` - Generated plots
- `data/reports/validation_report.md` - Final validation report

## Testing

Run the test suite:
```bash
python code/run_tests.py
```

Or with pytest directly:
```bash
pytest tests/
```

## Troubleshooting

- If you encounter memory issues, reduce the number of iterations in `code/main.py`
- For real data download failures, check your internet connection and UCI repository availability
- Ensure all required packages are installed as per `requirements.txt`
