# Quickstart: Calibration of Predictive Intervals for Time‑Series Forecasts

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM (required for full dataset processing; streaming enabled)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-713-calibration-of-predictive-intervals-for-
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `prophet` may require additional system dependencies (e.g., `build-essential` on Linux). Ensure your environment is prepared.*

## Data Preparation

The pipeline automatically downloads datasets on the first run.

1.  **Run the data fetcher**:
    ```bash
    python code/utils/checksum.py --download
    ```
    *This will attempt to download M4 and UCI Electricity from canonical sources (Hugging Face, with fallbacks). If a dataset is unavailable, it will log a fatal error.*

2.  **Verify checksums**:
    The script verifies the integrity of downloaded files against recorded hashes.

## Running the Pipeline

To run the full benchmark (ARIMA, Prophet, LSTM) on a **sample** (recommended for CI):

```bash
python code/evaluation/runner.py --sample-size [QUALITATIVE_SAMPLE_SIZE_DESCRIPTOR]
```

To run on the **full** dataset (may take >6 hours on CI):

```bash
python code/evaluation/runner.py
```

### Configuration
Edit `code/config.yaml` to adjust:
- `train_split_ratio`: Default **0.8**.
- `nominal_levels`: Default **[0.80, 0.95]**
- `lstm_epochs`: Default **50**
- `bootstrap_resamples`: Default **1000**.
- `sampling_strategy`: Default "stratified"

## Expected Outputs

After completion, check the `results/` directory:
- `coverage.csv`: Empirical coverage rates.
- `distributional_metrics.csv`: PIT and CRPS scores.
- `significance_test.csv`: Bootstrap p-values.
- `benchmark_timing.csv`: Runtime logs.

## Troubleshooting

- **OOM Error**: Ensure `--sample-size` is used. The pipeline streams data, but very large individual series may still spike memory.
- **LSTM Convergence Failure**: The pipeline logs "failed" series. Check `logs/runner.log` for details.
- **Dataset Download Failure**: Verify internet connectivity and check if the canonical URLs (M4/UCI) are still active.