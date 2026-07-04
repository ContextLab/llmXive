# Quickstart: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local environment with sufficient RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Data Ingestion
Run the ingestion script to download datasets.
```bash
python code/data_ingestion.py
```
*   This will check for paired data.
*   If unpaired, it will log a warning and prepare for Fallback Mode.

### Step 2: Preprocessing & Feature Extraction
```bash
python code/preprocessing.py
python code/feature_extraction.py
```

### Step 3: Modeling & Validation
```bash
python code/main.py
```
*   **Primary Mode**: Runs full statistical analysis.
*   **Fallback Mode**: Runs structural validation only. No statistical claims are made.

### Step 4: Review Output
Check `data/reports/` for:
*   `sensitivity_analysis.csv`
*   `model_results.json`
*   `pipeline_log.txt` (contains mode flags and warnings).

## Verification

To verify the pipeline runs correctly in a constrained environment:
```bash
pytest tests/contract/test_schemas.py
pytest tests/integration/test_pipeline.py
```

## Troubleshooting

*   **Memory Error**: If the process exceeds a substantial RAM threshold, the script will automatically downsample epochs. Ensure `NFR-001` constraints are met.
*   **Missing Data**: If the dataset is unpaired, the system will switch to Fallback Mode. Check `pipeline_log.txt` for the "Fallback Mode Active" warning.
*   **Underpowered**: If the available N is insufficient for the expected effect size, the report will be flagged as "Exploratory".