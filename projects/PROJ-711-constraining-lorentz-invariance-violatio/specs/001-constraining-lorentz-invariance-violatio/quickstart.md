# Quickstart: Constraining Lorentz Invariance Violation with Fermi Gamma‑Ray Burst Spectra

## Prerequisites

*   Python 3.11+
*   `pip`
*   Internet access (to download Fermi GBM data)
*   Sufficient disk space (for data and results)

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
    *(Note: `requirements.txt` will include `numpy`, `scipy`, `astropy`, `pandas`, `matplotlib`, `requests`, `pymc`, `arviz`, `pytest`)*

## Configuration

1.  **Set the random seed** (for reproducibility):
    Edit `code/config.py` and set `RANDOM_SEED = 42`.
2.  **Define the data directory**:
    Ensure `data/raw` and `data/processed` directories exist.

## Running the Pipeline

### Step 1: Data Ingestion
Download a representative sample of the brightest GRBs and their light curves.
```bash
python code/main.py --stage download --limit 30
```
*Output*: Files in `data/raw/`.

### Step 2: Preprocessing
Re-bin light curves and subtract background.
```bash
python code/main.py --stage preprocess
```
*Output*: `data/processed/*.csv` with columns `time_bins`, `net_counts`.

### Step 3: Lag Analysis
Compute spectral lags and bootstrap uncertainties.
```bash
python code/main.py --stage lag --bootstrap 1000
```
*Output*: `data/processed/lag_results.csv`.

### Step 4: LIV Constraint & Validation
Perform Hierarchical Bayesian regression and run a null test with a sufficient number of iterations to ensure statistical robustness.
```bash
python code/main.py --stage constraint --null-iterations 10000
```
*Output*: `results/global_constraint.json`, `results/null_distribution.csv`.

### Step 5: Generate Report
Generate the final analysis summary and plots.
```bash
python code/main.py --stage report
```
*Output*: `results/report.md`, `results/plots/`.

## Verification

To verify the pipeline with synthetic data:
```bash
python code/main.py --stage test --synthetic
```
This injects a known lag and verifies the system recovers it within the 95% CI.