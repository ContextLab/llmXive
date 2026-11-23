# Quickstart Guide

## Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## Setup

1. Clone the repository.
2. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline is executed via a series of stage scripts located in `code/scripts/`.

### 1. Project Structure Setup
```bash
python code/scripts/setup_project_structure.py
```

### 2. Data Ingestion
Downloads real data from verified sources (NOAA, Yahoo Finance, UK Grid).
```bash
python code/scripts/run_ingestion.py
```

### 3. Preprocessing
Handles missing values, stationarity (ADF/differencing/detrending), and resampling.
```bash
python code/scripts/run_preprocessing.py
```

### 4. Synthetic Data Generation
Generates fGn/ARFIMA series with known parameters.
```bash
python code/scripts/run_synthetic_grid.py
```

### 5. Metrics Calculation (Real)
Computes ACF, Hurst, Spectral Density for real data.
```bash
python code/scripts/run_metrics_real.py
```

### 6. Metrics Calculation (Synthetic)
Computes ACF, Hurst, Spectral Density for synthetic data.
```bash
python code/scripts/run_metrics_synthetic.py
```

### 7. Null Distribution Generation
Generates shuffled versions for real and synthetic data.
(Handled automatically in ingestion/synthesis steps or via specific scripts if separated)
```bash
# If a separate script exists, run it here. Otherwise, ensure T019a/b completed.
```

### 8. Hypothesis Testing
Runs Monte Carlo loop for Type I error estimation.
```bash
python code/scripts/run_hypothesis_testing.py
```

### 9. Regression Analysis
Regresses error rates against Hurst exponent.
```bash
python code/scripts/run_regression.py
```

### 10. Visualization
Generates plots for results.
```bash
python code/scripts/run_viz.py
```

### 11. Runtime Optimization (T066)
Profiles the Monte Carlo loop to ensure it meets the 6-hour limit.
```bash
python code/scripts/run_profile.py
```

## Verifying Results

Check `data/results/` for the following files:
- `final_summary.json`: Overall summary of the experiment.
- `regression_model.json`: Regression coefficients and diagnostics.
- `filtered_features.json`: List of features used in regression.
- `profile_report.json`: Performance profiling results.
- `baseline_status.json`: Status of the baseline validity check.

## Troubleshooting

- **Missing Data**: Ensure `run_ingestion.py` completed successfully and check `data/raw/`.
- **Stationarity Errors**: Check logs in `data/logs/` for series that failed ADF/detrending.
- **Runtime Issues**: Review `profile_report.json` to identify bottlenecks.
