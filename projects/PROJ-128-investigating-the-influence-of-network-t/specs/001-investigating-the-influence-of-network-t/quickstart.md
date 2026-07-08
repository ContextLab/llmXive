# Quickstart: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## 1. Prerequisites

*   Python 3.11+
*   `pip`
*   Access to the HCP 1200 Subjects Release (S1200) via the HCP website or AWS Open Data.

## 2. Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions compatible with CPU-only execution.*

## 3. Data Preparation

1.  Download the HCP 1200 Subjects Release (S1200) data. The pipeline expects data in `data/raw/`.
    *   **Option A (AWS)**: Use `aws s3 cp s3://hcp-openaccess/HCP_1200/ data/raw/ --recursive` (requires AWS CLI setup).
    *   **Option B (Web)**: Download preprocessed NIfTI files from the HCP Connectome Workbench and place them in `data/raw/`.
    *   Ensure the downloaded files match the checksums recorded in `state/projects/PROJ-128.../state.yaml`.

2.  Verify data integrity:
    ```bash
    python code/main.py --check-data
    ```

## 4. Running the Pipeline

Execute the full pipeline (structural metrics, dynamic metrics with LOO clustering, correlation, robustness):

```bash
python code/main.py
```

**Output**:
*   `data/processed/structural_metrics.csv`
*   `data/processed/dynamic_metrics.csv`
*   `data/processed/correlation_results.csv`
*   `data/logs/exclusion_log.json`
*   `reports/final_report.md`

## 5. Reproducibility Check

To verify reproducibility on a fresh environment:

```bash
# Set seed
export PYTHONHASHSEED=42

# Run pipeline
python code/main.py

# Verify outputs match expected hashes (if available)
python code/main.py --verify-hashes
```

## 6. Troubleshooting

*   **Memory Error**: Reduce the number of subjects or process in smaller batches (modify `config.py`).
*   **k-means Non-convergence**: This is expected for noisy data. The subject will be excluded and logged.
*   **No Significant Findings**: This is a valid result. The report will explicitly state that no associations survived FDR correction and frame the study as exploratory.
*   **Data Access**: If you cannot access HCP data, ensure you have a free account at `humanconnectome.org` and have accepted the data use agreement.