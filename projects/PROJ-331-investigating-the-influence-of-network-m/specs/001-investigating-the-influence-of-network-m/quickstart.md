# Quickstart: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Prerequisites
*   Python 3.11+
*   `pip` or `conda`
*   Access to HCP data (or a verified public subset/mirror).
*   ~14GB disk space (for processing, raw data is deleted).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-331-investigating-the-influence-of-network-m
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

## Configuration

Edit `code/config.py` to set:
*   `SUBJECT_IDS`: List of 50 HCP subject IDs (e.g., `['100106', '100208', ...]`).
*   `DATA_DIR`: Path to `data/` (default: `data/`).
*   `HCP_ACCESS_METHOD`: `aws` (default) or `openneuro` (fallback).
*   `SEED`: Random seed (default: 42).

## Running the Pipeline

Execute the full pipeline:

```bash
python code/pipeline.py
```

This script will:
1.  Download and process each subject sequentially (download -> process -> delete raw).
2.  Compute motif profiles and functional metrics.
3.  Run statistical analysis (correlations, Bonferroni, permutation).
4.  Generate `results.pdf` and `data/processed/subject_metrics.csv`.

## Verifying Results

1.  **Check Output Files**:
    *   `results/results.pdf`: The final report.
    *   `data/processed/subject_metrics.csv`: Aggregated data.
    *   `data/logs/pipeline.log`: Execution log.
    *   `results.json`: Contains the calculated success rate (SC-001).

2.  **Validate Schemas**:
    ```bash
    pytest tests/contract/
    ```

3.  **Reproducibility Check**:
    Run the pipeline again on a fresh environment. The output files should have identical checksums (if the same data is used).

## Troubleshooting

*   **Disk Space Error**: Ensure raw data is being deleted after processing. Check `pipeline.log` for "Deleting raw data" messages.
*   **HCP Access Error**: If credentials are missing, the pipeline will skip the subject and log a warning. Ensure `HCP_ACCESS_METHOD` is correctly set.
*   **Motif Counting Timeout**: If a subject takes >300s, the pipeline will abort and log a warning. This is unlikely for 3-node motifs on 100 nodes.

## Expected Output

*   **PDF Report**: Contains scatter plots, correlation coefficients, and p-values for each motif. **Includes** the mandatory disclaimer: "These findings are associational only and do not imply causation."
*   **CSV**: `subject_metrics.csv` with one row per subject.
*   **JSON**: `motif_profiles.json`, `global_efficiency.json`, `permutation_results.json`, `power_analysis.json`.