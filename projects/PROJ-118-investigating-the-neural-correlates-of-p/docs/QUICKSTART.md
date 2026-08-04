# Quickstart Guide

Get the MMN pipeline running in 5 steps.

## Step 1: Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENNEURO_API_KEY="your_key"
```

## Step 2: Download Data

```bash
python code/download.py
```
*Expected output: "Download complete. Checksums verified."*

## Step 3: Preprocess Data

```bash
python code/preprocess.py
```
*Expected output: "Preprocessing complete. Clean epochs saved to data/processed/epo_clean.fif"*

## Step 4: Extract Metrics

```bash
python code/extract.py
```
*Expected output: "Extraction complete. Metrics saved to results/metrics.csv"*

## Step 5: Analyze & Visualize

```bash
python code/stats.py
python code/viz.py
```
*Expected output: "Statistics saved to results/statistics.json. Plots saved to results/plots/"*

## Verification

Check the `results/` directory for:
- `metrics.csv` (contains participant data)
- `statistics.json` (contains p-values and effect sizes)
- `plots/erp_plot.png` (visual confirmation of MMN)

If any step fails, check the logs in the console output or specific log files in `data/processed/`.
