# Quickstart: Investigating Network Centrality in ASD Resting-State fMRI

## Prerequisites
- Python 3.11+
- Docker (for fMRIPrep)
- 14GB+ Disk Space
- 7GB+ RAM

## Installation

1. **Clone and Setup**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-460-investigating-the-impact-of-network-cent
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

2. **Verify Docker**
   ```bash
   docker pull jopet/fmriprep:latest
   ```

## Execution

### Step 1: Download Data
Run the download script. It will fetch metadata from the verified ABIDE parquet and attempt to download raw images.
```bash
python code/01_download.py
```
*Note: If the verified parquet links do not provide direct image downloads, this step will log the missing files and halt.*

### Step 2: Preprocess
Run fMRIPrep on the downloaded data.
```bash
python code/02_preprocess.py
```
*Warning: This step is CPU-intensive and may take several hours.*

### Step 3: Compute Centrality
Extract time-series, build graphs, and compute metrics.
```bash
python code/03_connectivity.py
python code/04_centrality.py
```

### Step 4: Statistical Analysis
Run t-tests, FDR correction, and sensitivity analysis.
```bash
python code/05_analysis.py
```

### Step 5: Classification & Visualization
Train classifier and generate brain plots.
```bash
python code/06_classification.py
python code/07_visualize.py
```

## Verification
Check `data/processed/results/` for statistical outputs and `data/processed/plots/` for visualizations.
Run tests:
```bash
pytest tests/
```
