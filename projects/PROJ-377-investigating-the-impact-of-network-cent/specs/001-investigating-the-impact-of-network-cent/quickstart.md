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

The pipeline is executed via the main script. It performs download, preprocessing, analysis, and validation in sequence.

```bash
python code/main.py
```

### Configuration

-   **Dataset URL**: The script uses the verified URL from `research.md`. This can be overridden via environment variable `DATASET_URL`.
-   **Atlas**: Default is AAL. Can be changed in `code/config.py` (if implemented) or passed as an argument.
-   **Random Seed**: Fixed at 42 (or defined in `code/utils/metrics.py`) for reproducibility.

### Output Artifacts

Upon successful completion, the following files will be generated in `data/processed/` and the root:

-   `data/processed/subjects.csv`: Cleaned subject data.
-   `data/processed/centrality_metrics.csv`: Calculated centrality scores.
-   `data/processed/model_results.json`: Regression and validation results.
-   `reproducibility_report.json`: Full pipeline metrics (wall clock time, RAM, checksums).
-   `figures/`: Scatter plots, permutation histograms, CV error plots.

## Troubleshooting

-   **Memory Error**: If you encounter `MemoryError`, ensure no other heavy processes are running and that the dataset is being processed in batches (check `code/data/preprocess.py`).
-   **Missing Columns**: If the script fails with "Missing behavioral data", the verified dataset URL does not contain the required motor task scores. See `research.md` for details.
-   **Network Timeout**: The download step may take time. Ensure stable internet connection.

## Validation

To verify the results:
1.  Check `reproducibility_report.json` for `wall_clock_time_seconds` < 21600 (6 hours).
2.  Check `data/processed/model_results.json` for `permutation_p_value` < 0.05 (if significant).
3.  Re-run `python code/main.py` and compare checksums of output files to ensure reproducibility.
