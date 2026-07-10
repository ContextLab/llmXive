# Quickstart: Statistical Properties of Integer Partitions

## Prerequisites

*   Python 3.11+
*   `pip`

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the scripts in `code/`.

### Step 1: Generate Partition Data
Computes exact counts and asymptotic baselines (Roth & Szekeres leading term).
```bash
python code/generate_partitions.py --n_max 50000
```
*Output*: `data/raw/partitions_raw.csv` (with SHA-256 checksum recorded in project state).

### Step 2: Engineer Features
Calculates residuals and *higher-order* density predictors.
```bash
python code/feature_engineering.py
```
*Output*: `data/processed/features.csv`

### Step 3: Fit Regression Model
Performs GAM regression, VIF check, and cross-validation.
```bash
python code/regression_model.py
```
*Output*: `data/processed/model_results.json`

### Step 4: Visualize Results
Generates plots of residuals vs. fitted values.
```bash
python code/visualize_results.py
```
*Output*: `data/visualizations/residuals_plot.png`

## Verification

Run the test suite to ensure correctness:
```bash
pytest tests/
```
*   `test_partition_logic.py`: Verifies exact counts for a representative range of $n$.
*   `test_pipeline.py`: Verifies runtime and memory constraints.

## Reproducibility

To ensure reproducibility, set the random seed before running any script that might involve randomness (e.g., cross-validation splits):
```bash
export PYTHONHASHSEED=0
export SEED=42
```
The scripts will read these environment variables.