# Quickstart: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   ~10 GB free disk space (for dataset caching and intermediate files).
-   Access to the internet (for initial dataset download).

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Running the Pipeline

The pipeline automatically detects data pairing and switches modes.

### Step 1: Data Ingestion & Preprocessing
Download and prepare the data. This step handles the mode switch logic.
```bash
python code/main.py --stage ingest_preprocess
```
-   **Expected Output**:
    -   If paired data found: "Primary Mode Active. Proceeding with analysis."
    -   If unpaired: "Warning: No paired data found. Switching to Fallback Mode. Primary research question ABANDONED."

### Step 2: Feature Extraction
Compute spectral and connectivity features.
```bash
python code/main.py --stage extract_features
```
-   **Expected Output**: `data/processed/feature_matrix.csv` (or parquet).

### Step 3: Modeling & Validation
Fit the Ridge regression model and run validation (permutation, FDR, sensitivity).
```bash
python code/main.py --stage model_validate
```
-   **Expected Output**: `reports/validation_report.json` containing R², p-values, and sensitivity tables.

### Step 4: Generate Reports
Compile the final analysis report.
```bash
python code/main.py --stage generate_report
```

## Verifying the Run

1.  **Check Logs**: Look for the `mode` flag in `code/logs/pipeline.log`.
2.  **Validate Schema**: Ensure `data/processed/feature_matrix.csv` matches `contracts/dataset.schema.yaml`.
3.  **Confirm Fallback Mode**: If the system entered Fallback Mode, verify that `reports/validation_report.json` contains `"flags": ["fallback_mode_active", "primary_question_abandoned"]` and that no biological claims are made.

## Troubleshooting

-   **Memory Error**: If the process crashes with OOM, reduce the `max_epochs_per_subject` in `code/config.py`.
-   **Missing Data**: If the download fails, verify network access to the HuggingFace URLs listed in `research.md`.
-   **Schema Mismatch**: Ensure the input Parquet files match the expected column names defined in the Data Model.
