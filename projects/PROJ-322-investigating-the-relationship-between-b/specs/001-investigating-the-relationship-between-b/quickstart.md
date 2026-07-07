# Quickstart: Investigating the Relationship Between Brain Network Reconfiguration and Recovery from Mild Traumatic Brain Injury

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local machine with ≥6GB RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-322-investigating-the-relationship-between-b
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `nilearn`, `networkx`, and `statsmodels` to ensure reproducibility.*

## Running the Pipeline

The pipeline is designed to run end-to-end on a GitHub Actions free-tier runner.

### 1. Data Ingestion (Phase 0)
Run the ingestion script to download and verify data.
```bash
python code/data_ingestion.py --dataset openneuro-fslr64k
```
*   **Output**: `data/raw/manifest.csv` and checksums.
*   **Check**: Verify that the log indicates "Memory OK" (≤6GB).
*   **Note**: If the dataset lacks cognitive scores, the pipeline will automatically switch to **Methodology Validation Mode** and generate synthetic data.

### 2. Preprocessing & Graph Metrics (Phase 1)
Process the data and compute metrics.
```bash
python code/graph_metrics.py --batch-size 5 --sparsity 0.15
```
*   **Output**: `data/processed/graph_metrics.csv`.
*   **Note**: If the dataset lacks mTBI labels or cognitive scores, this step will log a "Variable Fit Gap" and proceed with synthetic data for validation.

### 3. Statistical Analysis (Phase 2 & 3)
Run the LMM, permutation testing, and sensitivity analysis.
```bash
python code/statistical_model.py --permutations 1000 --sweep-thresholds
```
*   **Output**: `data/results/analysis_results.json`.
*   **Timeout**: The script will auto-stop if runtime exceeds 6 hours.
*   **Collinearity**: If VIF > 5 is detected, the script will automatically apply PCA or report descriptive statistics.

### 4. Verification
Check the output for robustness:
*   Verify `empirical_p_value` is close to `parametric_p_value` (if not synthetic).
*   Check `vif_flags` for any `> 5`.
*   Review `limitations` for sample size or missing data warnings.
*   **Critical**: Check `is_synthetic` flag. If `true`, no scientific claims should be made.

## Troubleshooting

*   **OOM Error**: Reduce `--batch-size` to 3 or 1 in `graph_metrics.py`.
*   **Model Non-Convergence**: The script will automatically skip the problematic subject and log the ID.
*   **Missing Data**: If no mTBI subjects are found in the dataset, the output will contain a "Methodology Validation Mode" flag per FR-009.
*   **Collinearity**: If VIF > 5, the script will use PCA or report descriptive statistics.
