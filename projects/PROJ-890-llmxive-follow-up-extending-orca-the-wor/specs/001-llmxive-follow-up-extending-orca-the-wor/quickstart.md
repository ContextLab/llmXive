# Quickstart: llmXive follow-up: extending "Orca: The World is in Your Mind"

## Prerequisites
- Python 3.11+
- 7GB+ RAM available
- Access to the verified HuggingFace dataset (network required for initial download)

## Setup

### 1. Environment Setup
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```
*Note: `requirements.txt` pins `torch` to a CPU-only version.*

### 2. Data Preparation
The pipeline expects the dataset to be available. Run the download script (or manually fetch the parquet):
```bash
python code/scripts/download_data.py
```
This will populate `data/raw/` with the necessary metadata and video references.

### 3. Run the Pipeline
Execute the main pipeline script which handles the dependency chain:
```bash
python code/main_pipeline.py
```
This script will:
1. Extract latents (with memory profiling).
2. Inject counterfactuals (Descriptive).
3. Run physics validation on a subset.
4. Filter ambiguous/unverified data.
5. Train models and compute statistics.

### 4. Verify Results
Check the output logs and results:
- `data/logs/audit.log`: Full pipeline execution log.
- `data/results/metrics.json`: Accuracy, p-values, and robustness scores.
- `data/results/validation_summary.csv`: Physics validation results.

## Troubleshooting

- **OOM Errors**: The script automatically reduces batch size. If it fails at batch=1, check `data/logs/audit.log` for specific memory usage patterns.
- **Missing Videos**: If video IDs are found but files are missing, the script logs the ID and continues. Ensure the source dataset is complete.
- **Physics Simulation Failures**: If `mujoco` fails to load, ensure the system has the required graphics libraries (headless mode is supported).
