# Quickstart: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local environment matching CPU constraints)

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

## Configuration

Edit `code/config.yaml` to set:
*   `random_seed`: Integer for reproducibility.
*   `window_size`: Default 30.
*   `stride`: Default 1.
*   `advi_max_iter`: Default 500.
*   `data_path`: Path to raw data or synthetic generation flag.

**Note**: Ensure `config.yaml` remains under 2KB. Do not store derived statistics here.

## Running the Pipeline

1.  **Generate/Download Data**:
    ```bash
    python code/src/data/download_datasets.py
    # OR for synthetic data:
    python code/src/data/synthetic_generator.py --inject-anomalies
    ```

2.  **Run the Anomaly Detection Pipeline**:
    ```bash
    python code/src/services/anomaly_detector.py
    ```
    This script will:
    *   Load and normalize data.
    *   Create sliding windows.
    *   Run DP-GMM (ADVI) and baselines.
    *   Compute metrics and statistical tests.
    *   Generate reports in `data/processed/results/`.

3.  **Verify Results**:
    Check `data/processed/results/posterior_trajectory.csv` for $\alpha$ derivatives.
    Check `data/processed/results/sensitivity_report.csv` for threshold analysis.

## Validation

To validate the pipeline:
1.  **Convergence Check**: Ensure no "WARNING: ADVI did not converge" logs appear for critical windows.
2.  **Resource Check**: Verify peak RAM < 7 GB and runtime < 6 hours (automated in CI).
3.  **Statistical Check**: Verify p-values for Wilcoxon and KS tests are present in the final report.

## Troubleshooting

*   **ADVI Convergence Failure**: Increase `advi_max_iter` in `config.yaml` or reduce window size.
*   **Memory Error**: Ensure no large datasets are loaded into RAM at once; use chunking if necessary.
*   **Config Size Error**: Move derived statistics to `state/` file if `config.yaml` exceeds 2KB.
