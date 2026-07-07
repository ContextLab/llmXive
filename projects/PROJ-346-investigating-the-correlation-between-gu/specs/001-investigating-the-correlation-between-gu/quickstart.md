# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

## Prerequisites

*   Python 3.11+
*   `pip` and `venv`
*   Git
*   14 GB disk space (temporary)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-346-investigating-the-correlation-between-gu
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or
    venv\Scripts\activate  # Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline consists of 7 sequential steps. Run them in order:

1.  **Ingest Data**:
    ```bash
    python code/01_ingest.py
    ```
    *Downloads AGP and NHANES data to `data/raw/`.*

2.  **Preprocess Data**:
    ```bash
    python code/02_preprocess.py
    ```
    *Filters microbiome, imputes cognitive data, saves to `data/processed/`.*

3.  **Check Data Linkage**:
    *   The pipeline automatically checks if individual-level data can be merged.
    *   If **merged**, it proceeds to Step 4.
    *   If **not merged**, it proceeds to Step 7 (Gap Report).

4.  **Run Correlation Analysis** (Conditional):
    ```bash
    python code/03_correlation.py
    ```
    *Computes Spearman correlations and FDR correction. Skipped if data gap detected.*

5.  **Run Regression** (Conditional):
    ```bash
    python code/04_regression.py
    ```
    *Skipped if individual-level linkage failed.*

6.  **Sensitivity Analysis** (Conditional):
    ```bash
    python code/05_sensitivity.py
    ```
    *Age stratification and normalization comparison. Skipped if data gap detected.*

7.  **Generate Visualizations** (Conditional):
    ```bash
    python code/06_visualize.py
    ```
    *Creates heatmap and forest plot in `results/`. Skipped if data gap detected.*

8.  **Generate Data Gap Report** (If Linkage Failed):
    ```bash
    python code/07_gap_report.py
    ```
    *Generates `data/gap_report.json` explaining the inability to perform correlation.*

## Output

*   **If Data Linked**:
    *   `data/processed/merged_dataset.parquet`
    *   `results/correlation_matrix.csv`
    *   `results/regression_coefficients.csv`
    *   `results/heatmap.png`
    *   `results/forest_plot.png`
*   **If Data Gap Detected**:
    *   `data/gap_report.json` (Detailed explanation of the data gap)
    *   `qc/linkage_failure_log.json`

## Troubleshooting

*   **Data Linkage Failure**: If `data/gap_report.json` exists, the pipeline has detected that no paired data is available. Check the report for details. This is the expected outcome for AGP + NHANES.
*   **Memory Error**: Reduce the sample size in `code/01_ingest.py` (e.g., `limit=5000`).
*   **Missing Variables**: If NHANES lacks cognitive tasks, the script will exit with a clear error message.
