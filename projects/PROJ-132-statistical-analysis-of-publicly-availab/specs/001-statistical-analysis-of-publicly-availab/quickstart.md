# Quickstart: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Prerequisites

*   Python 3.11+
*   `pip`
*   Access to the verified dataset URLs (for testing only) or local synthetic data generation.

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `geomstats` for Riemannian analysis and `statsmodels` for GAMMs.*

## Running the Pipeline

The pipeline is executed via `src/analysis/run_pipeline.py`.

### 1. Download & Preprocess (Test Mode)
Run with the `--test` flag to use **synthetic data** (since full EBD/PRISM URLs are not verified) instead of the full data.
```bash
python src/analysis/run_pipeline.py --test --seed 42
```
*   **Output**: `data/processed/test_sample.parquet`
*   **Expected**: A small dataset with grid-aligned phenology and climate metrics, using tail-preserving stratified sampling.

### 2. Model Fitting
Once data is prepared, run the GAMM fitting:
```bash
python src/models/gamm_fit.py --input data/processed/test_sample.parquet --output results/gamm_results.json
```
*   **Note**: This step uses a **Unified Spatial Model** (default spatial smooth) to avoid data snooping.

### 3. Trajectory Analysis
Analyze route shifts:
```bash
python src/models/trajectory.py --input results/gamm_results.json --output results/trajectories.json
```
*   **Note**: This step uses `geomstats` and propagates centroid uncertainty.

## Verification

Run the test suite to ensure data integrity and schema compliance:
```bash
pytest tests/
```
*   **Contract Tests**: Verify that output files match `contracts/*.schema.yaml`.
*   **Unit Tests**: Validate grid aggregation logic, missing data handling, and **tail-preserving sampling**.

## Troubleshooting

*   **Memory Error**: The synthetic datasets are small. If running on full data, ensure you have sufficient RAM or reduce the `--sample-rate` argument.
*   **Convergence Failure**: If GAMM fails to converge, check for collinearity in `results/diagnostics.csv`.
*   **Missing Data**: The pipeline automatically flags cells with "insufficient data" in the output logs.
*   **Riemannian Errors**: Ensure `geomstats` is installed and compatible with your numpy version.