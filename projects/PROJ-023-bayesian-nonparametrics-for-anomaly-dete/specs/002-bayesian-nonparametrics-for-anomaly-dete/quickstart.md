# Quickstart: Bayesian Nonparametrics for Anomaly Detection

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GitHub Actions (for CI execution) or a local machine with ~7GB RAM.

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-023-bayesian-nonparametrics-anomaly-dete
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run sequentially. Execute the following scripts in order:

### Step 1: Download Data
Fetches UCR/UCI time series data.
```bash
python code/scripts/download_data.py
```
*Output*: `data/raw/series.csv` (or `.parquet`)

### Step 2: Inject Anomalies
Creates synthetic anomalies and windowed datasets.
```bash
python code/scripts/inject_anomalies.py
```
*Output*: `data/processed/series_with_anomalies.csv`, `data/processed/ground_truth.csv`

### Step 3: Run Models
Execute the Bayesian GP and Baseline models.
```bash
# Run Bayesian Model
python code/scripts/bayesian_gp.py

# Run Baselines
python code/scripts/baseline_shewhart.py
python code/scripts/baseline_cusum.py
python code/scripts/baseline_vae.py
```
*Output*: `data/results/bayesian_predictions.csv`, `data/results/baseline_predictions.csv`

### Step 4: Evaluate & Visualize
Compute metrics and generate figures.
```bash
python code/scripts/evaluate.py
python code/scripts/render_fig1.py
python code/scripts/render_fig2.py
python code/scripts/sensitivity_analysis.py
```
*Output*: `data/results/evaluation.json`, `paper/figures/fig1_timeseries.png`, `paper/figures/fig2_method_comparison.png`

## Verification

To verify the installation and pipeline integrity:

1.  Check that `data/results/evaluation.json` exists and contains F1-scores for all models.
2.  Ensure `paper/figures/` contains the required PNG files.
3.  Run the unit tests:
    ```bash
    pytest code/tests/
    ```

## Troubleshooting

-   **OOM Error**: Reduce the window size in `inject_anomalies.py` or the number of inducing points in `bayesian_gp.py`.
-   **Convergence Warning**: If ELBO does not stabilize, increase the number of inference steps (FR-010) or adjust the learning rate.
-   **Dataset Not Found**: Verify internet connection and that the verified URLs in `download_data.py` match the current UCR/UCI mirrors.