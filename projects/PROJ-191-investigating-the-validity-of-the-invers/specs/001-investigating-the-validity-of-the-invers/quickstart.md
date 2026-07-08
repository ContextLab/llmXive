# Quickstart: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Prerequisites

-   Python 3.11+
-   `pip`
-   Access to arXiv supplementary materials (assumed accessible per spec).

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-191-investigating-the-validity-of-the-invers
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the main entry script `code/run_pipeline.py`.

### Step 1: Download and Harmonize Data
```bash
python code/run_pipeline.py --step download_harmonize
```
-   Downloads raw data from arXiv.
-   Converts units to SI.
-   Constructs covariance matrix.
-   Outputs: `data/processed/harmonized_dataset.*`

### Step 2: Run Inference (MCMC + Nested Sampling)
```bash
python code/run_pipeline.py --step inference
```
-   Runs `emcee` (a sufficient number of walkers, 5000 steps).
-   Runs `dynesty` for evidence.
-   Outputs: `data/results/posterior_samples.*`, `data/results/evidence.json`.

### Step 3: Run Robustness & Validation
```bash
python code/run_pipeline.py --step robustness
```
-   Performs leave-one-out, uncertainty inflation, injection-recovery, and null-simulation.
-   Outputs: `data/results/robustness_summary.json`.

### Step 4: Full Pipeline (End-to-End)
```bash
python code/run_pipeline.py --step all
```
-   Executes all steps in order.

## Verification

1.  **Check Convergence**:
    ```bash
    python code/run_pipeline.py --check convergence
    ```
    Verifies Gelman-Rubin < 1.01.

2.  **Validate Schemas**:
    ```bash
    pytest tests/contract/
    ```
    Ensures output files match `contracts/` schemas.

3.  **Reproducibility Check**:
    ```bash
    python code/run_pipeline.py --repro-check
    ```
    Re-runs with fixed seeds and compares checksums.

## Troubleshooting

-   **Runtime Error**: If the pipeline exceeds a reasonable duration threshold, reduce the number of robustness iterations in `code/config.py`.
-   **Covariance Error**: If the covariance matrix is not positive-definite, check the systematic error inputs in the raw data.
-   **Data Missing**: If arXiv downloads fail, verify network access and the specific arXiv supplementary URLs.
