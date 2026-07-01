# Quickstart: Evaluating Calibration of Predictive Intervals

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM (minimum), 14 GB disk space.

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-721-evaluating-calibration-of-predictive-int
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

The pipeline will automatically download the M4 dataset.

1.  **Run the download script**:
    ```bash
    python code/download.py
    ```
    *This fetches the M4 CSVs from the official GitHub repo and stores them in `data/raw/`.*

2.  **Verify data integrity**:
    Check that `data/raw/` contains the expected CSV files and that the checksum matches the recorded value in `state/`.

## Running the Pipeline

Execute the full evaluation pipeline on a representative subset of time series.:

```bash
python code/run_pipeline.py --subset-size 1000 --output results/
```

### Options
- `--subset-size`: Number of series to process (default: 1000).
- `--models`: Comma-separated list of models to run (default: `arima,ets,prophet,lightgbm`).
- `--horizons`: Comma-separated list of horizons (default: `1,2,3,4,5,6,7,8,9,10,11,12`).

## Expected Outputs

After completion, the following files will be generated in `results/`:

- `coverage.csv`: Empirical coverage rates for all models, horizons, and groups.
- `recalibration.csv`: Coverage rates after adaptive conformal prediction.
- `plots/`: Visualizations of coverage deviations and stratified analysis.

## Validation

To verify the pipeline ran correctly:

1.  **Check coverage rates**:
    ```bash
    python -c "import pandas as pd; df = pd.read_csv('results/coverage.csv'); print(df.groupby('model_name')['empirical_coverage_95'].mean())"
    ```
 Expected: Values should be close to (within [deferred] deviation).

2.  **Run unit tests**:
    ```bash
    pytest tests/unit/ -v
    ```

3.  **Run contract tests**:
    ```bash
    pytest tests/contract/ -v
    ```

## Troubleshooting

- **Model Convergence Failure**: The pipeline logs warnings for series where models fail. Check `logs/pipeline.log`.
- **Memory Error**: Reduce `--subset-size` (e.g., `--subset-size 500`).
- **LightGBM Slow**: Ensure `lightgbm` is installed from PyPI (CPU version) and not a GPU-specific build.
