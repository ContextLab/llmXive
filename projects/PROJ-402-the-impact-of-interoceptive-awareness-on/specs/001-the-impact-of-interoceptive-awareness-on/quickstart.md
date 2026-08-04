# Quickstart: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

## Prerequisites

*   Python 3.11+
*   `pip`
*   Internet connection (for dataset download)

## Installation

1.  **Clone the repository** and navigate to the project directory.
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

The pipeline is executed sequentially. Run the following commands in order:

### Step 1: Download Data
Downloads WESAD (Zenodo) and verifies checksums.
```bash
python code/01_download_data.py
```
*Output*: `data/raw/wesad/` (BIDS directory structure)

### Step 2: Audit Metadata
Scans for Schandry and TSST tasks.
```bash
python code/02_audit_metadata.py
```
*Output*: `results/data_audit.md` (Intermediate report)

### Step 3: Preprocess HRV (Conditional)
If the audit confirms data availability, this step calculates HRV.
```bash
python code/03_preprocess_hrv.py
```
*Output*: `data/derived/hrv_metrics.csv`

### Step 4: Analyze & Report
Runs regression or Feasibility Failure report generation and captures timing.
```bash
python code/04_analyze_regression.py
python code/06_capture_timing.py
```
*Output*: `results/data_audit.md` (Final), `results/regression_results.json`, `results/timing.log`

## Testing

Run the test suite to verify logic:
```bash
pytest tests/ -v
```

## Troubleshooting

*   **Missing Data**: If `data_audit.md` reports "Schandry Task: Missing", the regression step will automatically skip and generate a "Feasibility Failure" report. This is the expected outcome.
*   **Noisy Signals**: If HRV calculation fails for a subject, they are excluded, and a warning is logged in `results/logs/preprocess.log`.