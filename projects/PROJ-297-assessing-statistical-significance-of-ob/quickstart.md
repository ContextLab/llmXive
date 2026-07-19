# Quickstart Guide: Assessing Statistical Significance of Observed Correlations

## Prerequisites
- Python 3.9+
- pip
- Virtual environment (recommended)

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure `data/raw` and `output` directories exist (created by `code/config.py`).

## Running the Pipeline

### Step 1: Load and Verify Datasets
This step downloads UCI datasets, computes/stores SHA256 checksums, and cleans data.
```bash
python code/loaders.py --min-datasets 3
```

### Step 2: Run Full Analysis
Executes the full pipeline: correlation computation, graph construction, permutation testing (N=2000), BY correction, and reporting.
```bash
python code/main.py --threshold 0.3
```

### Step 3: Run Sensitivity Sweep
Re-runs permutation testing for multiple thresholds (0.1 to 0.5).
```bash
python code/main.py --threshold 0.3 --sweep
```

### Step 4: Verify Outputs
Check the generated files:
- `data/raw/checksums.json`: SHA256 hashes of raw files.
- `output/results/`: CSV summary of correlations and significance.
- `output/plots/`: Heatmaps and histograms.
- `output/reports/`: Sensitivity analysis and runtime logs.

## Troubleshooting
- **Data Download Failures**: Ensure internet access. If a dataset URL is invalid, check `code/config.py` for updated URLs.
- **Runtime Errors**: Check `output/reports/runtime_log.json` for timeout details.
- **Checksum Mismatches**: If a downloaded file is corrupted, delete it from `data/raw` and re-run `code/loaders.py`.
