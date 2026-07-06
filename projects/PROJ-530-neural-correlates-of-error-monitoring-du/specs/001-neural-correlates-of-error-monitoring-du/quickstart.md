# Quickstart: Neural Correlates of Error Monitoring

## Prerequisites

*   Python 3.11+
*   Git
*   Sufficient free disk space (for dataset and cache)

## Installation

1.  **Clone and Setup**
    ```bash
    cd projects/PROJ-530-neural-correlates-of-error-monitoring-du
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import mne; import statsmodels; print('Dependencies OK')"
    ```

## Running the Pipeline

### Step 1: Download Data
*Note: This step requires a valid dataset URL. If the verified URL is missing, this will generate synthetic data for testing. The Verified Accuracy gate is currently BLOCKED until a verified URL is provided.*
```bash
python code/download.py
```

### Step 2: Preprocess EEG
Applies filters, ICA, calculates angular deviation, and extracts MFN mean amplitudes.
```bash
python code/preprocess.py
```
*Output*: `data/processed/epochs_summary.parquet`, `data/preprocessing.yaml`

### Step 3: Run Analysis
Fits the Mixed-Effects model (or GAM via AIC comparison), performs sensitivity analysis, checks diagnostics, and validates compute feasibility.
```bash
python code/analysis.py
```
*Output*: `results/models/`, `results/diagnostics/`, `results/figures/`

### Step 4: Generate Report
(If a reporting script is added later)
```bash
python code/viz.py
```

## Testing

Run unit tests on a small subset:
```bash
pytest tests/ -v
```

## Troubleshooting

*   **Memory Error**: Ensure you are not loading the entire raw dataset into memory at once. The pipeline uses batch processing.
*   **Missing Dataset**: If `download.py` fails, check the `# Verified datasets` block in the research plan. A verified URL must be provided to proceed with real data.
*   **ICA Failure**: If ICA fails to converge, check the `data/preprocessing.yaml` for component logs.
*   **Feasibility Error**: If `analysis.py` raises a `FeasibilityError`, the runtime or memory exceeded the GitHub Actions free-tier limits (hours, GB). Review the `results/diagnostics/feasibility_report.json`.