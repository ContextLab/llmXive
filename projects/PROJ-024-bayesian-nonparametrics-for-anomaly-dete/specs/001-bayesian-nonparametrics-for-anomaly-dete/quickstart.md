# Quickstart: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Prerequisites

-   Python 3.11+
-   `git`
-   A GitHub account (for running on Actions, though local testing is supported).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Verify environment**:
    ```bash
    python -c "import pymc; import sklearn; print('Environment OK')"
    ```

## Running the Pipeline

### 1. Generate Synthetic Data
Since no verified real-world dataset with regime shifts is available, the pipeline starts by generating synthetic data.
```bash
python code/src/data/synthetic_generator.py --output data/raw/synthetic_timeseries.csv --anomaly-rate --length 2000
```

### 2. Run the Full Analysis
This executes the sliding window inference, baseline comparison, and statistical testing.
```bash
python code/src/main.py --config code/config.yaml
```
*Note: `main.py` orchestrates the flow: Data Load -> Windowing -> Inference -> Metrics -> Reporting.*

### 3. Inspect Results
Results are stored in `data/processed/`:
-   `posterior_trajectory.parquet`: The dynamic signatures ($\alpha$, $\dot{\alpha}$).
-   `detection_events.json`: Time-to-detection metrics.
-   `sensitivity_report.yaml`: Threshold analysis.
-   `figures/`: Generated plots (e.g., $\alpha$ trajectory, ROC curves).

## Configuration

Edit `code/config.yaml` to adjust hyperparameters (must remain <2KB):
```yaml
# code/config.yaml
seed: 42
window_size:
stride: 1
max_components: a finite set determined by the model's complexity constraints
advi_iters: a sufficient number of iterations to ensure convergence
thresholds: [low, 0.05, 0.1]
```

## Troubleshooting

-   **ADVI Convergence Warning**: If `WARNING: ADVI did not converge` appears, the window is skipped. Check `code/config.yaml` for `advi_iters` or try increasing it (trade-off with runtime).
-   **Memory Error**: Ensure no other heavy processes are running. The pipeline is designed for <7GB RAM.
-   **CUDA Error**: If you see CUDA errors, ensure `pymc` is not trying to use a GPU. The code explicitly forces CPU mode.

## Validation

Run the test suite to verify correctness:
```bash
pytest code/tests/ -v --cov=code/src
```