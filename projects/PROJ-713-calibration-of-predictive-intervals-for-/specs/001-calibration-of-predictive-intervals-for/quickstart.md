# Quickstart: Calibration of Predictive Intervals for Time‑Series Forecasts

## Prerequisites

-   Python 3.11+
-   Git
-   Sufficient RAM (recommended for full runs, streaming used for large datasets)

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-calibration-of-predictive-intervals
    cd projects/PROJ-713-calibration-of-predictive-intervals-for-/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import statsmodels, prophet, torch, properscoring; print('All dependencies installed.')"
    ```

## Running the Pipeline

### 1. Download Data
The pipeline expects data in `data/raw/`.
```bash
# Note: M4 and UCI Electricity download scripts are in code/scripts/download_data.py
# If the verified datasets block is used, this will download UCI HAR instead.
python code/scripts/download_data.py
```

### 2. Run Benchmark
Execute the main evaluation loop. This will process series sequentially.
```bash
# Run on a sample of M (500 series) and full UCI HAR
python code/evaluation/runner.py --dataset m4_sample --dataset uci_har --models arima prophet lstm
```

### 3. View Results
Results are saved to `results/`.
```bash
# View coverage summary
cat results/coverage_summary.csv

# View statistical significance
cat results/bootstrap_results.json
```

### 4. Generate Plots
```bash
python code/scripts/generate_plots.py --input results/coverage_summary.csv --output results/plots/
```

## Testing

Run the unit tests to verify metric calculations:
```bash
pytest tests/unit/ -v
```

Run the integration test (small subset):
```bash
pytest tests/integration/test_pipeline.py -v --sample-size 10
```

## Troubleshooting

-   **OOM Error**: Ensure `streaming=True` is set in `config.py` for large datasets.
-   **LSTM Failure**: Check `logs/` for "NaN detected" messages. The system will auto-retry with lower learning rate.
-   **Dataset Missing**: If M4/UCI-Elec is missing, the system will fall back to UCI HAR (verified) and log a warning.
