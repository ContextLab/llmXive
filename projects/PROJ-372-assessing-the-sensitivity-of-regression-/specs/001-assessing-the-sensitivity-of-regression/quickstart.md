# Quickstart: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for dataset download)

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
    *Dependencies include: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `datasets`.*

## Running the Pipeline

The pipeline is executed via the CLI entry point.

1.  **Run the full experiment**:
    ```bash
    python src/cli.py run --datasets 10 --subsets 200 --tiers 5
    ```
    This will:
    - Download verified datasets.
    - Profile them (Breusch-Pagan, Cook's, Condition Number).
    - Run the resampling loop.
    - Fit the meta-regression model.
    - Save results to `data/` and `artifacts/`.

2.  **Run a specific step** (e.g., just profiling):
    ```bash
    python src/cli.py profile
    ```

3.  **Run tests**:
    ```bash
    pytest tests/
    ```

## Expected Output

- `data/profiles.json`: Summary of dataset properties.
- `data/stability_results.json`: Empirical SDs for all subsets.
- `artifacts/meta_analysis.json`: Final interaction term results.
- `logs/execution.log`: Detailed logs of skipped singular subsets and download checksums.

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, ensure no other heavy processes are running. The code attempts to stream data, but large Parquet files may still require significant RAM.
- **Singularity Warnings**: It is normal to see warnings about singular matrices for small subsets. The code handles these gracefully.
- **Dataset Download Failures**: If a verified URL returns 404, the script will log the error and skip that dataset, continuing with the others.
