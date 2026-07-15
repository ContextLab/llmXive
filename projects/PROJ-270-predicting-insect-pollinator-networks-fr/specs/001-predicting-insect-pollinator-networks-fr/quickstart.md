# Quickstart: Predicting Insect Pollinator Networks

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the Web of Life database (open access) and Dryad (open access).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-270-predicting-insect-pollinator-networks-fr
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Setup

The pipeline expects data to be downloaded automatically.

1.  **Run the ingestion script**:
    ```bash
    python code/ingestion.py --ecosystems 10
    ```
    *   This will attempt to download interaction matrices for 10 ecosystems and their associated trait data.
    *   Data will be saved to `data/raw/`.
    *   *Note*: If trait data is missing for an ecosystem, it will be skipped and logged.

2.  **Verify data**:
    Check `data/raw/` for CSV files. Ensure at least 8 ecosystems have complete trait data.

## Running the Pipeline

Execute the full pipeline (Ingest -> Process -> Train -> Validate -> Report):

```bash
python code/main.py
```

### Steps Performed:
1.  **Preprocessing**: Imputes missing values, normalizes traits, encodes categories.
2.  **Training**: Trains a Random Forest with 5-fold stratified CV.
3.  **Validation**: Tests on a held-out ecosystem and compares to a null model.
4.  **Reporting**: Generates `results/report.md` and plots in `results/plots/`.

## Output Artifacts

*   `data/processed/feature_matrix.csv`: The unified training data.
*   `results/model.pkl`: The trained Random Forest model.
*   `results/metrics.json`: AUC-ROC, importance scores, p-values.
*   `results/report.md`: Human-readable summary of findings.
*   `results/plots/`: Network visualizations (observed vs. predicted).

## Troubleshooting

*   **Missing Data**: If the script reports "Insufficient trait data for X ecosystems", check the `data/raw/` logs. The pipeline will proceed with the remaining valid ecosystems.
*   **Memory Error**: If running on a small machine, reduce the number of target ecosystems or use the `--streaming` flag (if implemented) to process data in chunks.
*   **Network Error**: The ingestion script retries failed downloads. Ensure internet access is available.
