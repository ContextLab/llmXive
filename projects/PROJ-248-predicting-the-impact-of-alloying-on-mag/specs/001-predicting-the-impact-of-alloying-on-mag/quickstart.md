# Quickstart: Predict Saturation Magnetization of Alloys (OQMD Data)

This guide walks you through a **single CI run** that produces a surrogate model for **saturation magnetization** using the publicly verified OQMD magnetic CSV, evaluates it, generates a feature‑importance report, and exposes a CLI for single‑alloy prediction.

> **Scope Note** – Only saturation magnetization is modeled because no verified open source provides Curie temperature. If a Curie‑temperature dataset becomes available, the pipeline can be extended accordingly. The prediction JSON schema still contains a `curie_temperature` field, which will be set to `null` pending data.

## Prerequisites
- GitHub Actions runner (free tier) **or** a local Linux environment with **Python 3.11**.
- No API keys required (OQMD CSV is publicly downloadable).

## 1. Clone the Repository & Install Dependencies
```bash
git clone <repo‑url>
cd PROJ-248-predicting-the-impact-of-alloying-on-mag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Download the OQMD Dataset
```bash
python code/download_datasets.py
```

This script creates:
- `data/raw_oqmd.csv` (OQMD magnetic CSV)  
- `data/data_sources.yaml` (manifest with URL, SHA‑256 checksum, and download timestamp)

> **Note**: The script uses the verified HuggingFace URL `https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv` and the `datasets` library to stream the CSV, guaranteeing successful download on the CI runner.

## 3. Run the End‑to‑End Pipeline (Saturation Magnetization)
```bash
python -m src.models.train \
    --target saturation_magnetization \
    --dataset oqmd \
    --output_dir artifacts \
    --log_dir logs
```

**What happens**
1. Loads the OQMD magnetic CSV from the verified URL.  
2. Cleans the dataset (standardizes formulas, removes missing fields, resolves duplicates).  
3. Engineers features (fractional elemental abundances, elemental‑average properties, crystal descriptors).  
4. Performs a 5‑fold GridSearchCV (≤ 30 min) for Random Forest and Gradient Boosting regressors.  
5. Selects the best model by R², saves it as `artifacts/model_saturation.pkl`.  
6. Writes `metrics/metrics_saturation.json` (R², MAE, RMSE) for the internal test split.  
7. Samples 200 distinct OQMD alloys **not** seen during training, evaluates the model, and appends external metrics to the same JSON file.  
8. Conducts a paired Wilcoxon signed‑rank test against a Linear Regression baseline (Bonferroni‑corrected α = 0.05).  
9. Generates feature‑importance CSV and PNG (`reports/feature_importance_saturation.*`).  
10. Uploads all artifacts as GitHub Actions artifacts.

## 4. Inspect Results
```bash
# Internal & external metrics
cat metrics/metrics_saturation.json

# Feature‑importance plot
display reports/feature_importance_saturation.png
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
    --model artifacts/model_saturation.pkl \
    --input example_alloy.json \
    --output prediction.json
```

`prediction.json` will contain:
```json
{
  "saturation_magnetization": 1.34,
  "curie_temperature": null,
  "confidence_interval": {
    "saturation_magnetization": [1.20, 1.48]
  }
}
```
The prediction completes in **≤ 2 seconds** on the CI runner and conforms to the **original** `contracts/prediction.schema.yaml` (both fields present; `curie_temperature` is `null`). If a Curie‑temperature dataset becomes available, the CLI will automatically include a numeric value.

## 6. Artifact Publishing (GitHub Actions)
The workflow `ci.yml` automatically uploads:
- `data/cleaned_oqmd.csv`  
- `artifacts/model_saturation.pkl`  
- `metrics/metrics_saturation.json`  
- `reports/feature_importance_saturation.*`  
- `contracts/prediction.schema.yaml`  
- `data/data_sources.yaml`

These artifacts enable reproducibility checks by downstream reviewers.

## 7. Extending the Pipeline
If a verified open dataset containing Curie temperature becomes **available**, add it to `code/download_datasets.py`, extend the cleaning step, and repeat the training pipeline for the new target.

---



