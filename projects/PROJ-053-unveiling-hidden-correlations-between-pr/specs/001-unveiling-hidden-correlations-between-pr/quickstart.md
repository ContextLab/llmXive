# Quickstart: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Prerequisites
- Python 3.11 or newer
- `git`
- Internet connection (to download the dataset, if an appropriate open source is supplied)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-053-unveiling-hidden-correlations-between-pr

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Pipeline

All pipeline steps are invoked via `code/main.py` with the `--step` flag. Each step writes logs under `results/`.

### 1. Download & Validate the Dataset
```bash
python code/main.py --step download
```
- Downloads a **public AM‑alloy dataset** that **must** contain the exact columns `laser_power`, `scan_speed`, `layer_thickness`, `alloy_composition`, `yield_strength`, and `ductility`.  
- Verifies SHA‑256 checksum (recorded in `state/dataset_checksum.txt`).  
- Confirms ≥ 50 rows and presence of all required columns. If any column is missing, the script aborts with a clear error: *“Insufficient or malformed dataset: required column X missing.”*  

### 2. Preprocess the Data & Create Train/Test Splits
```bash
python code/main.py --step preprocess
```
- Median imputes missing values.  
- Min‑max normalizes all numeric columns to `[0, 1]`.  
- Detects and drops zero‑variance columns (logged).  
- One‑hot encodes `alloy_composition` (creates `alloy_<type>` binary columns).  
- Splits into `data/processed/train.csv` and `data/processed/test.csv`.  
- Writes `data/processed/preprocessing.log`.

### 3. Train Models & Compute Metrics
```bash
python code/main.py --step train
```
- Trains GPR (RBF kernel) with 5‑fold CV and a Linear Regression baseline.  
- Saves models under `results/model/`.  
- Writes `results/metrics.json` (validated against `contracts/model_output.schema.yaml`), which now **includes** the permutation‑importance ranking under `feature_importance`, the `residual_analysis` object, and the `power_analysis` entry.

### 4. Analyse Importance (merged into metrics)
```bash
python code/main.py --step importance
```
- Computes permutation importance (30 repeats, `random_state=42`).  
- Merges the resulting ranking directly into `results/metrics.json` as the `feature_importance` array.

### 5. Power Analysis (integrated)
```bash
python code/main.py --step power_analysis
```
- Performs the bootstrap‑based power analysis using the **effective sample size** after preprocessing and records the minimum detectable R² (with confidence interval) inside `results/metrics.json`.

### 6. Generate Visualizations
```bash
python code/main.py --step visualize
```
- Produces contour plot of predicted **Yield Strength** vs. **Laser Power** and **Scan Speed** (axes correspond to the normalized variables).  
- Produces uncertainty heatmap with red zones for σ > 2 × median σ.  
- Writes side‑car JSON metadata for each plot (`results/visualization/*.json`).

### 7. Review Outputs
- `results/metrics.json` – performance numbers, importance ranking, residual analysis, uncertainty ratio, runtime, and power‑analysis note.  
- `results/plots/contour_yield_strength.png` – predicted surface.  
- `results/plots/uncertainty_heatmap.png` – σ heatmap.  
- `results/confounders.json` – any potential confounder flags (high predictor‑response correlation, VIF warnings).  
- `state/manifest.yaml` – manifest of all primary artifacts for traceability.

## Expected Runtime
On the GitHub Actions free tier the full pipeline typically finishes **[deferred]** for a dataset of ≤ 500 samples, well within the allotted time limit (SC‑005).

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `Dataset download failed` | Network issue or checksum mismatch | Verify internet connectivity; delete `data/raw/<dataset>.csv` and re‑run `--step download`. |
| `Insufficient data for GPR training; minimum 50 samples required.` | Downloaded file corrupted, missing rows, or columns filtered out during preprocessing | Re‑run the download step; the script will abort with a clear error if the row count is < 50 or required columns are absent. |
| `Zero variance detected in column X` | All rows share the same value for a predictor | The column is automatically dropped; check `preprocessing.log` for details. |
| `Model artifact missing` | Previous step crashed (e.g., out‑of‑memory) | Inspect `results/*.log`; ensure the CI runner has ≤ 7 GB RAM. |
| `metrics.json missing key rmse_percentage_range` | Older version of the code; update | Re‑run `--step train`; the key is now generated correctly. |

---


