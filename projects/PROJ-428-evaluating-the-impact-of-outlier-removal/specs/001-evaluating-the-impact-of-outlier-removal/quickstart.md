# Quickstart: Evaluating the Impact of Outlier Removal Methods on Variance Estimation

## Prerequisites

-   Python 3.11+
-   `pip`
-   Access to the verified datasets (via internet for initial download, or cached locally).

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-428-evaluating-the-impact-of-outlier-removal/code
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, and `linearmodels` are installed.

## Running the Simulation

### 1. Generate Data and Run Analysis
Execute the main simulation script. This will:
-   Download/Load datasets (if not cached).
-   Generate synthetic data with known ground truth parameters.
-   Inject outliers.
-   Apply removal methods (IQR, Winsorization, Trimming).
-   Compute metrics.
-   Run statistical tests (LMM, Holm-Bonferroni).
-   Generate plots.

```bash
python run_simulation.py
```

**Default Behavior**:
-   Runs multiple replicates per condition (Strictly enforced).
-   Uses all distribution types.
-   Saves results to `data/processed/results.csv`.
-   Saves plots to `data/processed/plots/`.

### 2. Check Results
After completion, inspect the output:
-   `data/processed/results.csv`: Raw results for every replicate.
-   `data/processed/summary_stats.csv`: Aggregated Bias/MSE per method/condition.
-   `data/processed/plots/interaction_plot.png`: Visual comparison of methods.
-   `data/processed/statistical_test.txt`: LMM and Holm-Bonferroni results.

### 3. Validate Contracts
Run the contract tests to ensure data compliance:
```bash
pytest tests/test_contracts.py
```

## Troubleshooting

-   **Runtime Error**: If the script exceeds a feasible duration threshold, the project is flagged as infeasible. The script will **not** reduce replicates to 50. Check logs for "TIMEOUT EXCEEDED" messages.
-   **Missing Data**: If a specific UCI dataset fails to load, the script will skip it and log a warning, proceeding with the remaining datasets.
-   **Memory Error**: Ensure no other heavy processes are running. The script is designed to process one condition at a time to minimize RAM usage.