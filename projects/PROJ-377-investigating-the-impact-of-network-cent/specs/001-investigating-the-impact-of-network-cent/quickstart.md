# Quickstart: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

## Prerequisites

-   Python 3.11+
-   pip
-   Sufficient disk space (~5-10 GB for temporary data)
-   Internet access (to download the dataset)

## Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-377-investigating-the-impact-of-network-cent
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
    *Note: `requirements.txt` will pin versions of `pandas`, `numpy`, `networkx`, `scikit-learn`, `statsmodels`, `nilearn`, `matplotlib`.*

## Running the Pipeline

The pipeline is executed stepwise. It performs download, validation, preprocessing, analysis, and validation in sequence.

```bash
# Phase 0: download (T001) and fatal metadata gate (T002)
python code/data/download.py
python code/data/validate_metadata.py
```

The remaining phases (preprocessing, centrality, regression, permutation
validation, reporting) are run by their respective module entry points
under `code/data/`, `code/analysis/`, and `code/utils/`, in the task
order defined in `tasks.md`.

### Configuration

-   **Dataset URL**: The script uses the verified URL from `research.md`. This can be overridden via environment variable `DATASET_URL`.
-   **Atlas**: Default is AAL. Can be changed in `code/config.py` (if implemented) or passed as an argument.
-   **Random Seed**: Fixed at 42 (or defined in `code/utils/metrics.py`) for reproducibility.

## Output Artifacts

Upon successful completion, the following files are generated in `data/processed/` and the root:

-   `data/raw/metadata.csv`: Downloaded subject metadata (validated by the T002 fatal gate).
-   `data/processed/behavioral/retention_metrics.json`: Retention metrics (T003).
-   `data/processed/behavioral/power_metrics.json`: Power check metrics (T004a).
-   `data/processed/behavioral/subject_scores.csv`: Behavioral scores per subject (T017).
-   `data/processed/centrality/*.csv`: Centrality metrics, global scores, VIF, model predictors.
-   `data/processed/regression/*.csv`: Regression summaries.
-   `data/processed/validation/*`: Permutation and cross-validation results.
-   `reproducibility_report.json`: Full pipeline metrics (wall clock time, RAM, checksums).
-   `figures/`: Scatter plots, permutation histograms, CV error plots.

## Troubleshooting

-   **Memory Error**: If you encounter `MemoryError`, ensure no other heavy processes are running and that the dataset is being processed in batches (check `code/data/preprocess.py`).
-   **Missing Columns**: If the script fails with "Fatal: Dataset lacks behavioral motor task metrics", the verified dataset does not contain the required motor task scores. See `research.md` for details. This is a hard stop by design (T002).
-   **Network Timeout**: The download step may take time. Ensure stable internet connection.

## Validation

To verify the results:
1.  Check `reproducibility_report.json` for `wall_clock_time_seconds` < 21600 (6 hours).
2.  Check permutation/CV result JSONs under `data/processed/validation/` for `permutation_p_value` < 0.05 (if significant).
3.  Re-run the pipeline steps and compare checksums of output files to ensure reproducibility.