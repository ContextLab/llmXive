# Quickstart: llmXive follow-up: extending "Intern-Atlas: A Methodological Evolution Graph as Research Infrastruct"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the Intern-Atlas graph snapshot (downloaded manually or via script if URL is verified).
*   Access to Retraction Watch Database (downloaded manually or via script if URL is verified).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-815-llmxive-follow-up-extending-intern-atlas
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

4.  **Verify data availability**:
    Ensure `data/raw/intern-atlas-graph.parquet` (or equivalent) and `data/raw/retraction-database.csv` exist. If not, download them from the verified sources and place them in `data/raw/`.

## Running the Pipeline

The pipeline is orchestrated by `code/main.py`.

1.  **Run the full pipeline**:
    ```bash
    python code/main.py
    ```
    This will:
    *   Extract and filter the graph (2010-2018).
    *   Compute features (BRR, Entropy).
    *   Map to retraction labels.
    *   Train models (Topological & Baseline).
    *   Run robustness checks (Permutation n=100, Threshold Sweep, VIF/MI).
    *   Output results to `results/metrics.yaml`.

2.  **Run a specific step** (e.g., feature engineering only):
    ```bash
    python code/features.py --input data/raw/filtered-graph.parquet --output data/derived/features.csv
    ```

3.  **Run tests**:
    ```bash
    pytest tests/
    ```

## Expected Output

*   `results/metrics.yaml`: Contains AUC-ROC, coefficients, VIF, MI, and FPR/FNR for each threshold.
*   `results/plots/`: Contains PR curves and threshold sensitivity plots.
*   `data/derived/labeled_dataset.csv`: The final dataset used for modeling.

## Troubleshooting

*   **"No ground truth labels found"**: Ensure the retraction database covers the 2010-2018 window.
*   **"Memory Error"**: The graph may be too large. Check `code/config.py` for sampling parameters.
*   **"VIF > 5"**: This is a warning flag, not a failure. The model is still run, but the result is flagged as potentially unstable in the report.
