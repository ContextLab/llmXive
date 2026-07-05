# Quickstart: Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis

## Prerequisites

-   Python 3.11 or higher
-   `pip` package manager
-   Sufficient disk space (approx. tens of gigabytes for raw prime data up to $10^{10}$)
-   Internet access (for downloading verified datasets)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-548-exploring-the-relationship-between-prime
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

## Running the Pipeline

The pipeline is designed to run in stages. You can run the full pipeline or individual components.

### 1. Generate/Ingest Data

**Option A: Use Verified LMFDB Data (Recommended)**
```bash
python code/data/ingest_zeros.py --source lmfdb
python code/data/generate_primes.py --source lmfdb --max_n [upper_bound]
```

**Option B: Generate Primes Locally (If LMFDB data is incomplete)**
```bash
python code/data/generate_primes.py --mode sieve --max_n [large-scale upper bound]
```
*Note: This may take several hours.*

### 2. Preprocess Data
```bash
python code/data/preprocess.py
```
This script computes normalized gaps and spacings and saves them to `data/processed/`.

### 3. Run Analysis
```bash
python code/analysis/distribution_test.py
```
This performs the KS test against the GUE distribution.

### 4. Run Robustness Checks
```bash
python code/analysis/robustness.py
```
This runs the sensitivity analysis across different window sizes.

### 5. Run Monte Carlo Simulation
```bash
python code/analysis/monte_carlo.py
```
This generates the Cramér model null distribution.

## Verifying Results

After running the pipeline, check the `results/` directory:
-   `correlation_results.json`: Contains the primary KS statistic and p-value.
-   `robustness_report.md`: Contains the sensitivity analysis results.
-   `plots/`: Contains visualizations of the distributions.

## Troubleshooting

-   **OOM Errors**: If you encounter Out of Memory errors during prime generation, reduce the `--chunk_size` parameter in `generate_primes.py`.
-   **Data Missing**: If the LMFDB dataset download fails, verify your internet connection and the validity of the URL in `research.md`. Do not attempt to generate zeta zeros locally unless explicitly authorized by a spec amendment.
