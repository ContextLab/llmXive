# Quickstart: Detecting Statistical Power Drift in Replicated Studies

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions runner (or local environment with 7GB+ RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r src/requirements.txt
    ```
    *Note: `requirements.txt` will be generated during the implementation phase.*

## Running the Analysis

### Option 1: Full Pipeline (Recommended)

Run the entire analysis from data download to final report:

```bash
python -m src.cli.main run-full
```

This will:
1.  Download the OSF datasets from the verified HuggingFace URLs.
2.  Calculate post-hoc power for all studies.
3.  Fit the Linear Mixed-Effects Model (LMM).
4.  Run the 10,000-iteration permutation test.
5.  Generate the final JSON report and plots.

### Option 2: Step-by-Step

1.  **Download Data**:
    ```bash
    python -m src.cli.main download-data
    ```
    *Output: `data/raw/osf_replication_data.csv`*

2.  **Calculate Power**:
    ```bash
    python -m src.cli.main calculate-power
    ```
    *Output: `data/derived/power_estimates.csv`*

3.  **Run Drift Analysis**:
    ```bash
    python -m src.cli.main run-drift-analysis --permutations 10000
    ```
    *Output: `results/drift_report.json`, `results/null_distribution.csv`*

4.  **Generate Visualizations**:
    ```bash
    python -m src.cli.main generate-plots
    ```
    *Output: `results/power_drift_scatter.png`, `results/null_dist_hist.png`*

## Output Artifacts

Upon completion, the following files will be available:

-   `data/derived/power_estimates.csv`: Post-hoc power for every study.
-   `data/derived/residuals.csv`: Residual power values for visualization.
-   `results/drift_report.json`: Final statistical results (slopes, p-values, confidence intervals).
-   `results/null_distribution.csv`: Permutation test results.
-   `results/power_drift_scatter.png`: Visualization of residual power vs. year.
-   `results/summary.md`: Human-readable summary of findings.

## Troubleshooting

-   **Memory Error**: If the permutation test runs out of memory, reduce the iteration count:
    ```bash
    python -m src.cli.main run-drift-analysis --permutations 1000
    ```
-   **Dataset Download Failure**: Ensure your network allows access to `huggingface.co`. If behind a proxy, set `HTTPS_PROXY` environment variable.
-   **Missing Fields**: The script will skip rows with missing data. Check `logs/cleaning.log` for details on dropped studies.
-   **Convergence Warning**: If the LMM fails to converge, check `logs/model_fit.log` for details. The script will attempt to simplify the random effects structure automatically.