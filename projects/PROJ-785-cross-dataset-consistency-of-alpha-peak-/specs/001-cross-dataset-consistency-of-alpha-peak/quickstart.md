# Quickstart: Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG

## Prerequisites

*   Python 3.11+
*   Git
*   At least 20 GB free disk space (for raw data download and processing)
*   Internet connection (for OpenNeuro download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-785-cross-dataset-consistency-of-alpha-peak-/code
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the `main.py` orchestration script.

### Step 1: Download and Preprocess
Downloads a subset of OpenNeuro datasets and applies both pipelines.
```bash
python main.py --stage download_preprocess
```
*   **Output**: `data/raw/`, `data/derivatives/`
*   **Note**: This may take a variable duration depending on network speed.

### Step 2: Estimate APF
Calculates APF using both methods for all preprocessed data.
```bash
python main.py --stage estimate_apf
```
*   **Output**: `data/processed/apf_estimates.csv`

### Step 3: Statistical Analysis
Runs the mixed-effects model, bootstrapping, simulation-based power analysis, and sensitivity sweep.
```bash
python main.py --stage analysis
```
*   **Output**: `data/processed/model_results.json`, `data/processed/sensitivity_analysis.csv`, `data/processed/plots/`

### Step 4: Generate Report
Generates the final summary report and figures, including SC-002 and SC-003 validation status.
```bash
python main.py --stage report
```

## Verification

To verify the installation and data integrity:

1.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/ -v
    ```
2.  **Check Data Checksums**:
    Ensure `state/projects/PROJ-785-...yaml` contains valid SHA256 hashes for `data/raw`.

## Troubleshooting

*   **"RAM Exceeded" Error**: The script automatically switches to sequential processing. If it fails, reduce the `--subjects-per-dataset` flag in `config.py`.
*   **"OpenNeuro Connection Failed"**: Check internet connection. The script implements a retry mechanism with a limited number of attempts before failing.
*   **"No Alpha Peak Found"**: This is expected for some subjects. Check `data/processed/apf_estimates.csv` for `status="Indeterminate"`.
*   **"API Fetch Failed"**: If the OpenNeuro API is unreachable, the system halts with a "Data Integrity" error.

## Expected Output

*   **Forest Plot**: `data/processed/plots/forest_apf_by_dataset.png`
*   **Variance Bar Chart**: `data/processed/plots/variance_components.png`
*   **Sensitivity Table**: `data/processed/sensitivity_analysis.csv`
*   **Validation Report**: `data/processed/validation_summary.json` (Includes SC-002 Pass/Fail and SC-003 Power Status)