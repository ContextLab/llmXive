# Quickstart: Evaluating Calibration of Probabilistic Weather Forecasts

## Prerequisites

*   Python 3.11+
*   `pip` or `conda`
*   Git

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `pymc`, `properscoring`, `diebold-mariano`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`.*

## Running the Pipeline

The pipeline is executed via the main entry point. It handles data download, alignment, baseline calculation, isotonic recalibration, and (if possible) Bayesian recalibration.

```bash
python src/main.py
```

### Configuration

Edit `src/utils/config.py` to adjust:
*   `DATA_SOURCE`: Set to "subseasonal_rodeo" or "noaa_gfs".
*   `TRAIN_SPLIT_RATIO`: Default 0.7.
*   `BAYESIAN_TIMEOUT_MINUTES`: Default 60.
*   `SEED`: Random seed for reproducibility (Default: 42).

### Expected Outputs

Upon successful completion, the `results/` directory will contain:
*   `results_baseline.csv`: Brier/CRPS for raw forecasts.
*   `results_isotonic.csv`: Metrics after isotonic recalibration.
*   `results_bayesian.csv`: Metrics after Bayesian recalibration (or fallback status).
*   `figures/`: Reliability diagrams and PIT histograms.
*   `logs/pipeline.log`: Detailed execution logs.

## Troubleshooting

*   **"Data Availability Gate Failed"**: The dataset lacks `probability_value` fields. Check the `DATA_SOURCE` config. If using NOAA/GFS, ensure the correct files are downloaded.
*   **"Bayesian Model Timeout"**: The MCMC sampler exceeded 60 minutes. The pipeline will fallback to Isotonic results. Check `logs/pipeline.log` for R-hat diagnostics.
*   **"Memory Error"**: The dataset is too large for RAM. Ensure `streaming=True` is enabled in `src/data/loaders.py`.
