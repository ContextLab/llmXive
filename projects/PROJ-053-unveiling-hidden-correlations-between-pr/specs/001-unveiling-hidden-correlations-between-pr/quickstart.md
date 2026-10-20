# Quickstart: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Prerequisites
- Python 3.11 or newer
- `git`
- Internet connection (to download the dataset)

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

### 1. Download & Validate the Dataset
```bash
python code/main.py --step download
```
- Downloads `doe.csv` from the verified URL.
- Verifies SHA‑256 checksum.
- Checks that at least 50 rows and the required numeric columns are present.

### 2. Preprocess the Data
```bash
python code/main.py --step preprocess
```
- Median imputes missing values.
- Min‑max normalizes all numeric columns to `[0, 1]`.
- Writes `data/processed/preprocessed.csv` and `data/processed/preprocessing.log`.

### 3. Train Models & Compute Metrics
```bash
python code/main.py --step train
```
- Splits data (80 % train / 20 % test, fixed random seed 42).
- Trains GPR (RBF kernel) with 5‑fold CV and a Linear Regression baseline.
- Saves models under `results/model/`.
- Writes `results/metrics.json` (validated against `contracts/model_output.schema.yaml`).

### 4. Analyse Importance & Uncertainty
```bash
python code/main.py --step analyze
```
- Computes permutation importance (`results/importance_ranking.json`).
- Generates high‑uncertainty flag CSV (`results/high_uncertainty_regions.csv`).
- Produces contour and uncertainty heatmap PNGs under `results/plots/`.
- Writes side‑car JSON metadata for each plot (`contracts/visualization.schema.yaml`).

### 5. Review Outputs
- `results/metrics.json` – performance numbers, uncertainty ratio, runtime.  
- `results/plots/contour_response.png` – predicted surface.  
- `results/plots/uncertainty_heatmap.png` – σ heatmap with red zones for σ > 2×median.  
- `results/importance_ranking.json` – ranked feature influence.

## Expected Runtime
On the GitHub Actions free tier the full pipeline typically finishes in **≈ 3 minutes** for the ~200‑row dataset, well within the 6‑hour limit (SC‑005).

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `No verified open dataset found` | Dataset URL unreachable or checksum mismatch. | Verify internet connectivity; re‑run `--step download`. |
| `Insufficient data for GPR training; minimum 50 samples required.` | Downloaded file has < 50 rows. | Check the raw file; if corrupted, delete `data/raw/doe.csv` and re‑run download. |
| `Zero variance detected in column X` | All rows share the same value for a predictor. | The column is automatically dropped; no further action needed. |
| `Model artifact missing` | Previous step failed (e.g., training crashed). | Inspect `code/main.py` logs; ensure the CI runner has enough memory (≤ 7 GB). |

---
