# Quickstart: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

## Prerequisites

*   Python 3.11 or higher.
*   `pip` and `virtualenv` (or `conda`).
*   Access to the OpenML API (no key required for public datasets, but rate limits apply).

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-504-evaluating-the-impact-of-variable-select
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
    *Note: `requirements.txt` pins versions for reproducibility (e.g., `scikit-learn==1.4.0`, `statsmodels==0.14.1`).*

## Running the Pipeline

The main execution script is `code/main.py`.

### Step 1: Download Datasets
This step fetches 10 valid regression datasets from OpenML and saves them to `data/raw/`.
```bash
python code/main.py --action download
```
*   **Output**: `data/raw/datasets.json` and `data/raw/openml_*.csv`.
*   **Verification**: Check `data/raw/datasets.json` to ensure 10 datasets are marked "valid".

### Step 2: Run Simulations
This step generates synthetic outcomes and runs the variable selection methods.
```bash
python code/main.py --action simulate --workers 2 --seed 42
```
*   **Parameters**:
    *   `--workers`: Number of parallel processes (default 2, matches CI).
    *   `--seed`: Base seed for reproducibility (default). **This seed is passed to `simulators.py` to ensure deterministic outcome generation.**
*   **Output**: Chunked Parquet files in `data/simulated/` and a summary log.
*   **Note**: This is the most time-consuming step (approx. several hours on CI).

### Step 3: Aggregate & Analyze
This step computes recovery metrics, runs Friedman/Mixed-Effects tests, and generates plots.
```bash
python code/main.py --action analyze
```
*   **Output**:
    *   `results/simulation_results.csv` (Dataset-level aggregates)
    *   `results/plots/recovery_curve_snr.png`
    *   `results/plots/recovery_curve_sparsity.png`
    *   `results/statistical_tests.json`

### Step 4: Verify Results
Run the test suite to ensure the pipeline executed correctly.
```bash
pytest tests/ -v
```

## Reproducibility

To reproduce the exact results of a previous run:
1.  Ensure the same `requirements.txt` is used.
2.  Set the `--seed` flag to the original seed value.
3.  The `download` action will re-fetch the same OpenML datasets (canonical sources).

## Troubleshooting

*   **API Timeout**: If `download` fails, check your internet connection. The script includes retry logic, but persistent failures may require manual dataset download.
*   **Memory Error**: If `simulate` crashes with OOM, reduce the number of parallel workers (`--workers 1`) or process datasets sequentially.
*   **Singular Matrix**: If a specific dataset causes errors, it may be skipped automatically due to collinearity. Check `data/raw/datasets.json` for the "skipped_collinearity" status.