# Quickstart: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Prerequisites
-   Python 3.11+
-   `pip`
-   Access to a terminal with internet connectivity (for arXiv downloads).

## Installation

1.  **Clone and Setup Environment**
    ```bash
    cd projects/PROJ-191-investigating-the-validity-of-the-invers/code/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import emcee, dynesty, numpy; print('All dependencies OK')"
    ```

## Running the Pipeline

### Step 1: Data Download & Harmonization
Download raw data and generate the harmonized dataset with covariance matrix.
```bash
python main.py --step download_harmonize
```
*Output*: `data/harmonized/dataset_v1.csv`, `data/harmonized/covariance_v1.npz`.

### Step 2: Bayesian Inference
Run MCMC and Nested Sampling.
```bash
python main.py --step infer
```
*Output*: `results/inference_run_001.json`, `results/samples_run_001.h5`.

### Step 3: Robustness Analysis
Run LOO, Injection-Recovery, and Null-Simulation.
```bash
python main.py --step robustness
```
*Output*: `results/robustness_report.json`.

### Step 4: Full Pipeline (Recommended)
Run all steps in sequence.
```bash
python main.py --all
```

## Validation
Run the test suite to ensure correctness.
```bash
pytest tests/
```

## Troubleshooting
-   **Memory Error**: If the covariance matrix is too large, the pipeline will automatically subsample the data points to fit 7GB RAM. Check `logs/memory_log.txt` for details.
-   **Convergence Warning**: If Gelman-Rubin > 1.01 after 5000 steps, the pipeline will extend the run. If it exceeds 5.5 hours, it will log a warning and proceed.
