# Quickstart: Predicting Plant Herbivore Resistance

## Prerequisites

*   Python 3.11+
*   `pip`
*   Access to GitHub Actions (for CI) or a local environment with limited RAM resources.

## Installation

1.  Clone the repository and navigate to the project directory:
    ```bash
    cd projects/PROJ-407-predicting-plant-herbivore-resistance-fr
    ```
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via a single entry point script.

### Step 1: Ingest Data
Attempt to download the specified dataset (e.g., GSE12345) or a verified fallback.
```bash
python code/ingest.py --accession GSE12345 --output data/raw/
```
*Note: If the real dataset is unavailable, this step will fail gracefully with a clear error message.*

### Step 2: Preprocess
Normalize, impute, and validate the data.
```bash
python code/preprocess.py --input data/raw/GSE12345_raw.csv --output data/processed/
```

### Step 3: Train & Validate
Train the model and run permutation testing.
```bash
python code/model.py --input data/processed/GSE12345_processed.csv --output data/processed/
python code/validation.py --input data/processed/GSE12345_processed.csv --model data/processed/GSE12345_model.pkl --output data/processed/
```

### Step 4: Generate Report
Compile results into the final summary.
```bash
python code/report.py --input data/processed/ --output results/
```

## Verification

To verify the pipeline runs correctly:
1.  Check `results/summary_report.md` for the "Statistically Significant" flag.
2.  Verify `data/processed/GSE12345_results.json` contains a `permutation_p_value` < 0.05 (if signal exists).
3.  Ensure `data/raw/` contains the original file and its `.sha256` checksum.

## Troubleshooting

*   **"No quantifiable resistance metric found"**: The dataset metadata lacks a numeric resistance score. The pipeline cannot proceed.
*   **"Download failed"**: Network timeout or NCBI GEO unreachable. Retry up to 3 times (automatic).
*   **"Memory Error"**: Dataset too large. The pipeline is optimized for ≤500 samples. If exceeded, it will attempt PCA or fail.
