# Quickstart: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Prerequisites

-   Python 3.11 or higher
-   `pip` package manager
-   Access to the internet (for downloading datasets)
-   ~14 GB disk space (for raw data and intermediate files)

## Installation

1.  **Clone the Repository** (or navigate to the project root).
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `scikit-learn`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `datasets`, `pyyaml`, `statsmodels`.*

## Project Structure

```text
.
├── code/                 # Source code
│   ├── main.py           # Entry point
│   ├── .flake8           # Linter config
│   └── ...
├── data/                 # Data directory (created on first run)
├── results/              # Output directory (created on first run)
└── tests/                # Test suite
```

## Running the Pipeline

### 1. Full Pipeline Execution

Run the entire pipeline from download to aggregation:

```bash
python code/main.py --config code/config.yaml
```

**What this does**:
-   Downloads datasets from verified URLs.
-   Computes checksums.
-   Filters datasets (normality, sample size, skew/kurtosis).
-   Generates simulated data (null & alternative).
-   Applies transformations.
-   Runs Type I error simulations (null) and Power simulations (alternative).
-   Aggregates results, runs GLMM, and sweeps alpha.
-   Generates plots.
-   Saves logs and state.

### 2. Step-by-Step Execution

#### Download and Filter
```bash
python code/data/downloaders.py
python code/data/filters.py
```

#### Transform and Test
```bash
python code/data/transformations.py
python code/utils/statistical_tests.py
```

#### Simulate and Aggregate
```bash
python code/data/simulations.py
python code/analysis/aggregation.py
```

### 3. Running Tests

Run the unit and integration tests to verify correctness:

```bash
pytest tests/ -v
```

### 4. Checkpointing

If the pipeline is interrupted, resume from the last checkpoint:

```bash
python code/main.py --resume
```

The checkpoint file is located at `results/checkpoint.json` (schema: `current_dataset_id`, `last_seed`, `processed_count`).

## Verifying Results

1.  **Check Logs**:
    ```bash
    cat results/pipeline.log
    ```
2.  **Inspect Aggregated Results**:
    ```bash
    cat results/aggregated_results.csv
    ```
3.  **View Plots**:
    Open `results/figures/error_rates.png` and `results/figures/power_curves.png`.

## Troubleshooting

-   **Missing Datasets**: Ensure network access and verify URLs in `data/datasets.csv`.
-   **Transformation Failures**: Check `data/imputation_log.csv` for skipped variables.
-   **Runtime Errors**: Ensure you have enough disk space and memory (streaming is enabled by default via `pandas.read_csv(chunksize=...)` and `datasets.load_dataset(streaming=True)`).
-   **Checksum Mismatch**: Verify the SHA-256 hash in `data/checksums.csv` matches the downloaded file.
-   **GLMM Convergence**: If GLMM fails to converge, check for extreme class imbalance in the simulated data.
