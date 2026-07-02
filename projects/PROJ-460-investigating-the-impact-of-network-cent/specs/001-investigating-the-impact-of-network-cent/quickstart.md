# Quickstart: Investigating Network Centrality in ASD Resting-State fMRI

## Prerequisites

*   Python 3.11+
*   `pip`
*   `git`
*   (Optional) Docker (for local full fMRIPrep runs, not required for CI)

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-460-investigating-the-impact-of-network-cent
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import networkx; import nilearn; import sklearn; print('All dependencies OK')"
    ```

## Running the Pipeline

### Option A: Real Data Mode (Required)
Downloads pre-processed ABIDE derivatives from OpenNeuro and runs the full analysis.
```bash
python code/main.py --mode real --dataset ds0002800 --participants 20
```
*   **Note**: This mode requires network access to OpenNeuro. If the dataset is unavailable, the script will **fail gracefully** with an error message. **No synthetic data is generated.**

### Option B: Local Data Mode (For existing derivatives)
Uses pre-downloaded derivatives in `data/raw/`.
```bash
python code/main.py --mode local --participants 20
```

## Key Scripts

*   `code/download.py`: Handles data acquisition from OpenNeuro.
*   `code/graph_analysis.py`: Computes centrality metrics.
*   `code/statistics.py`: Runs t-tests, FDR correction, and sensitivity analysis.
*   `code/classification.py`: Trains logistic regression.
*   `code/viz.py`: Generates brain surface plots.

## Expected Outputs

1.  **`data/derived/centrality_metrics.csv`**: Centrality values for all participants and ROIs.
2.  **`data/derived/group_comparison.csv`**: T-stats, p-values, q-values.
3.  **`data/derived/classification_results.json`**: Accuracy, AUC, CV metrics.
4.  **`data/derived/preprocessing_log.yaml`**: Provenance and success rate.
5.  **`data/derived/collinearity_diagnostics.yaml`**: Pairwise correlations.
6.  **`data/derived/sensitivity_analysis.yaml`**: Threshold sweep results.
7.  **`figures/centrality_map.png`**: Brain surface visualization of significant nodes.

## Troubleshooting

*   **Data Unavailable**: If OpenNeuro is inaccessible, the pipeline fails. Ensure network connectivity or use `--mode local` with pre-downloaded data.
*   **Memory Error**: Reduce `--participants` or use a smaller subset.
*   **Disconnected Graph**: The script logs a warning and proceeds with the top 15% threshold; if still disconnected, it logs the count of isolated nodes.
