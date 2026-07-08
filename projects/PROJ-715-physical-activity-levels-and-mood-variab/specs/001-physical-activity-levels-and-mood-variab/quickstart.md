# Quickstart: Physical Activity Levels and Mood Variability in Daily Life

## Prerequisites

-   Python 3.11+
-   Git
-   Access to HuggingFace (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd specs/001-physical-activity-mood-variability
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

## Running the Pipeline

The pipeline consists of three main stages: Ingestion, Preprocessing, and Analysis.

### 1. Ingest Data
Download the StudentLife dataset, verify integrity, and compute checksums.
```bash
python code/ingest.py
```
*Output*: `data/raw/bronze.parquet` (and checksum file).

### 2. Preprocess Data
Aggregate raw logs into daily metrics, deriving sleep and affect if necessary.
```bash
python code/preprocess.py
```
*Output*: `data/processed/daily_aggregates.csv`.

### 3. Run Analysis & Generate Report
Fit models, perform cross-validation, and generate the PDF/HTML report.
```bash
python code/analysis.py
python code/report.py
```
*Output*: `data/processed/model_results.json`, `reports/analysis_report.html`.

## Validation

To verify the pipeline against the contract schemas:
```bash
pytest tests/contract/
```

## Troubleshooting

-   **Dataset Download Failed**: Ensure you have internet access. The script uses the verified HuggingFace URL. If the URL changes, update `code/config.py`.
-   **Convergence Warning**: If `statsmodels` reports non-convergence, check `data/processed/daily_aggregates.csv` for participants with only 1-2 days of data. These may need exclusion.
-   **Memory Error**: If running out of RAM, ensure no other heavy processes are running. The dataset is small, but `pandas` loading can be optimized by using `dtype` specifications.
