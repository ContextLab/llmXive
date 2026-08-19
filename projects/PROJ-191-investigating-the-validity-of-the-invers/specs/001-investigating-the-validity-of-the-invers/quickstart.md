# Quickstart: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions runner (or local environment with 7 GB+ RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-191-investigating-the-validity-of-the-invers
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

4.  **Verify linting setup**:
    ```bash
    ruff check code/
    black --check code/
    ```

## Running the Pipeline

### Step 1: Download and Harmonize Data
This step downloads the arXiv supplementary materials, converts units to SI, and constructs the covariance matrix.
```bash
python code/download.py
python code/harmonize.py
```
*Outputs*: `data/processed/harmonized_dataset.csv`, `data/processed/covariance_matrix.npy`

### Step 2: Run Bayesian Inference
This step runs the MCMC sampler (`emcee`) and nested sampling (`dynesty`).
```bash
python code/inference.py
```
*Outputs*: `data/results/mcmc_chains.npy`, `data/results/evidence.json`

### Step 3: Robustness and Validation
This step performs leave-one-out cross-validation and injection-recovery tests.
```bash
python code/robustness.py
```
*Outputs*: `data/results/robustness_report.json`, `data/results/injection_recovery.png`

## Verifying Results

1.  **Check Convergence**: Ensure the Gelman-Rubin statistic in `evidence.json` is $< 1.01$.
2.  **Validate Schemas**:
    ```bash
    pytest tests/contract/
    ```
3. **Review Constraints**: Check `data/results/robustness_report.json` for the [deferred] credible upper limits on $\alpha$.

## Troubleshooting

-   **Data Download Failed**: Verify internet access. The script expects arXiv supplementary files to be available. If missing, the script will exit with a clear error.
-   **MCMC Non-Convergence**: If the Gelman-Rubin statistic is $> 1.01$, the script will log a warning. Check `data/results/mcmc_chains.npy` for chain behavior.
-   **Memory Error**: If RAM exceeds 7 GB, reduce the number of walkers or steps in `code/inference.py` (configurable via environment variables).
