# Quickstart: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Prerequisites

-   Python 3.11 or higher.
-   Git.
-   Sufficient RAM (recommended for safety, though a specific memory limit is the target).

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-799-statistical-properties-of-integer-partit
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
    *Dependencies include: `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `pytest`, `statsmodels`.*

## Running the Pipeline

The full pipeline can be executed via the main entry point:

```bash
python code/main.py
```

This script will:
1.  Generate primes up to 50,000 (if not present).
2.  Compute exact partition counts $p_{\mathcal{P}}(n)$ (in batches).
3.  Compute asymptotic baseline $Q_{as}(n)$.
4.  Calculate features and residuals.
5.  Fit the regression model (with Null Model comparison).
6.  Generate the visualization plot.
7.  Save all artifacts to `data/processed/`.

### Individual Steps

If you wish to run steps individually:

1.  **Generate Partitions**:
    ```bash
    python code/generate_partitions.py
    ```
    *Output: `data/processed/partition_counts.csv`*

2.  **Compute Baseline**:
    ```bash
    python code/compute_baseline.py
    ```
    *Output: `data/processed/baseline_values.csv`*

3.  **Feature Engineering**:
    ```bash
    python code/feature_engineering.py
    ```
    *Output: `data/processed/features.csv`*

4.  **Fit Model**:
    ```bash
    python code/fit_model.py
    ```
    *Output: `data/processed/model_results.json`*

5.  **Visualize**:
    ```bash
    python code/visualize.py
    ```
    *Output: `data/processed/residuals_plot.png`*

## Verification

Run the test suite to ensure correctness:

```bash
pytest tests/ -v
```

Key tests include:
-   `test_dp_logic`: Verifies partition counts for small $n$.
-   `test_features_non_null`: Ensures `features.csv` has no missing values.
-   `test_baseline_formula`: Validates the asymptotic formula against known approximations.

## Expected Outputs

After running the pipeline, check `data/processed/` for:
-   `features.csv`: The primary dataset for analysis.
-   `model_results.json`: Statistical metrics ($R^2$, p-values).
-   `residuals_plot.png`: Visual confirmation of the systematic bias.
