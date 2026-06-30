# Quickstart: Investigating the Neural Response to Deviance in Auditory Perception

## Prerequisites

*   Python 3.11+
*   Git
*   14 GB free disk space
*   Internet connection (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-118-investigating-the-neural-correlates-of-p
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

## Running the Pipeline

The pipeline is executed in stages. Ensure you have sufficient disk space before starting.

### Step 1: Download Data
```bash
python code/download.py
```
*   **Action**: Fetches `ds003645` from OpenNeuro.
*   **Retry Logic**: Automatically retries 3 times with 10s backoff on failure.
*   **Output**: `data/raw/`

### Step 2: Preprocess Data
```bash
python code/preprocess.py
```
*   **Action**: Filters (1-30 Hz), re-references, epochs (-200 to 600 ms), and runs ICA.
*   **Output**: `data/processed/epo.fif`

### Step 3: Extract Metrics (Difference Wave)
```bash
python code/extract.py
```
*   **Action**: Computes Deviant - Standard difference waves. Finds peak amplitude/latency in 150-250 ms window.
*   **Note**: Participants with no peak are flagged but retained.
*   **Output**: `results/metrics.csv`

### Step 4: Statistical Analysis
```bash
python code/stats.py
```
*   **Action**: Runs t-tests on difference scores, FDR correction, 10k cluster permutation tests, and mixed-effects models.
*   **Output**: `results/statistics.json`

### Step 5: Generate Visualizations
```bash
python code/viz.py
```
*   **Action**: Creates ERP plots (Standard, Deviant, Difference) and topographic maps.
*   **Output**: `results/plots/`

## Verification

Run the test suite to ensure the pipeline is functioning correctly:
```bash
pytest tests/
```

## Troubleshooting

*   **Memory Error**: Ensure you have closed other applications. The pipeline subsamples to a reduced number of channels to fit available RAM.
*   **Download Failed**: Check internet connection. The script will retry automatically.
*   **No MMN Peak**: If no peak is found in 150-250 ms, the participant is flagged as `peak_detected=false` but included in prevalence counts, not excluded from the study.
