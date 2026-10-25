# Quickstart: Predicting Magnetic Properties of Alloys (OQMD + Materials Project)

This guide walks you through a **single CI run** that produces surrogate models for **both** saturation magnetization and Curie temperature using publicly verified datasets, evaluates them, generates feature‑importance reports, and exposes a CLI for single‑alloy prediction.

> **Scope Note** – Both targets are now modeled; the pipeline requires the verified Materials Project bulk archive (v2026.09) in addition to the OQMD magnetic CSV.

## Prerequisites
- GitHub Actions runner (free tier) **or** a local Linux environment with **Python 3.11**.
- No API keys required (both datasets are publicly downloadable).

## 1. Clone the Repository & Install Dependencies
```bash
git clone <repo‑url>
cd PROJ-248-predicting-the-impact-of-alloying-on-mag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Download the Datasets
```bash
python src/services/data_fetch.py
```

This script creates:
- `data/raw_oqmd.csv` (OQMD magnetic CSV)  
- `data/raw_mp.zip` (Materials Project bulk archive)  
- `data/data_sources.yaml` (manifest with URLs, SHA‑256 checksums, and download timestamps)

## 3. Run the End‑to‑End Pipeline (Both Targets)
```bash
python -m src.models.train \
    --targets saturation_magnetization curie_temperature \
    --datasets oqmd mp \
    --output_dir artifacts \
    --log_dir logs
```

**What happens**
1. Loads both OQMD and Materials Project datasets from the verified URLs.  
2. Cleans each dataset (standardizes formulas, removes missing fields, resolves duplicates).  
3. Engineers features (fractional elemental abundances, elemental‑average properties, crystal descriptors).  
4. Performs a 5‑fold GridSearchCV (≤ 30 min per target) for Random Forest and Gradient Boosting regressors.  
5. Selects the best model for each target by R², saves them as `artifacts/model_saturation.pkl` and `artifacts/model_curie.pkl`.  
6. Writes `metrics/metrics_saturation.json` and `metrics/metrics_curie.json` (R², MAE, RMSE) for internal test splits.  
7. Samples 200 distinct alloys **not** seen during training from OQMD (saturation) and Materials Project (Curie) and evaluates the models, appending external metrics to the same JSON files.  
8. Conducts paired Wilcoxon signed‑rank tests against Linear Regression baselines for **both** targets, applying a Bonferroni‑corrected α = 0.0125.  
9. Generates feature‑importance CSV and PNG for each target (`reports/feature_importance_{target}.*`).  
10. Uploads all artifacts as GitHub Actions artifacts.

## 4. Inspect Results
```bash
# Internal & external metrics
cat metrics/metrics_saturation.json
cat metrics/metrics_curie.json

# Feature‑importance plots
display reports/feature_importance_saturation.png
display reports/feature_importance_curie.png
```

## 5. Single‑Alloy Prediction (CLI)
Create `example_alloy.json`:
```json
{
  "composition": "Fe2Ni",
  "spacegroup": 225,
  "lattice_parameters": {
    "a": 3.58,
    "b": 3.58,
    "c": 3.58,
    "alpha": 90,
    "beta": 90,
    "gamma": 90
  }
}
```

Run the prediction:
```bash
python -m src.cli.predict \
    --model_saturation artifacts/model_saturation.pkl \
    --model_curie artifacts/model_curie.pkl \
    --input example_alloy.json \
    --output prediction.json
```

`prediction.json` will contain:
```json
{
  "saturation_magnetization": "value to be determined in the experimental phase",
  "curie_temperature": "on the order of several hundred degrees",
  "confidence_interval": {
    "saturation_magnetization": [1.20, 1.48],
    "curie_temperature": [580.0, 660.0]
  }
}
```
The prediction completes in **≤ 2 seconds** on the CI runner and conforms to `contracts/prediction.schema.yaml`.

## 6. Artifact Publishing (GitHub Actions)
The workflow `ci.yml` automatically uploads:
- `data/cleaned_oqmd.csv`  
- `data/cleaned_mp.csv`  
- `artifacts/model_saturation.pkl`  
- `artifacts/model_curie.pkl`  
- `metrics/metrics_saturation.json`  
- `metrics/metrics_curie.json`  
- `reports/feature_importance_saturation.*`  
- `reports/feature_importance_curie.*`  
- `contracts/prediction.schema.yaml`  
- `data/data_sources.yaml`

These artifacts enable reproducibility checks by downstream reviewers.

## 7. Extending the Pipeline
If additional magnetic descriptors become available (e.g., anisotropy), simply add them to the feature‑engineering module and rerun the training command with the new target list.

---

