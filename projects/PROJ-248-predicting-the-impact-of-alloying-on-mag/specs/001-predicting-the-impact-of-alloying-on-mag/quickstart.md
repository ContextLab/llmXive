# Quickstart: Predict Saturation Magnetization of Alloys (OQMD Data)

This guide walks you through a **single CI run** that produces a surrogate model for **saturation magnetization** using the publicly verified OQMD magnetic dataset, evaluates it, generates a feature‑importance report, and exposes a CLI for single‑alloy prediction.

> **Scope Note** – Only saturation magnetization is modeled because no open source provides Curie temperature. The prediction JSON schema still contains a `curie_temperature` field; the CLI will output `null` for this field with a logged warning.

## Prerequisites
- GitHub Actions runner (free tier) **or** a local Linux environment with **Python 3.11**.
- No API keys required (datasets are publicly downloadable).

## 1. Clone the Repository & Install Dependencies
```bash
git clone <repo‑url>
cd PROJ-248-predicting-the-impact-of-alloying-on-mag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Download the Dataset
```bash
python code/download_datasets.py
```

The script now:
- Downloads the **OQMD magnetic CSV** from the verified HuggingFace URL (`).  
- Writes `data/raw_oqmd.csv` and records its SHA‑256 checksum in `data/data_sources.yaml`.

## 3. Run the End‑to‑End Pipeline (Saturation Magnetization)
```bash
python -m src.models.train \
    --target saturation_magnetization \
    --dataset oqmd \
    --output_dir artifacts \
    --log_dir logs
```

**What happens**
1. Loads the OQMD magnetic CSV.  
2. Cleans the dataset (standardizes formulas, discards missing fields, resolves duplicates).  
3. Engineers **fractional elemental abundances** and **element‑wise averages** of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus, plus crystal‑structure descriptors.  
4. **Calibration step**: applies a linear scaling factor to `magnetic_moment` based on an experimental benchmark (if available) to correct systematic DFT bias.  
5. Performs a **5‑fold GridSearchCV** (≤ 30 min) for Random Forest and Gradient Boosting regressors.  
6. Selects the best model by R², saves it as `artifacts/model_saturation.pkl`.  
7. Writes `metrics/metrics_saturation.json` (R², MAE, RMSE) for the internal test split.  
8. **External validation** uses a hold‑out set of **200** distinct alloys from a **different OQMD release** (e.g., OQMD v2026.09) and appends external metrics to the same JSON file.  
9. Conducts **two paired Wilcoxon signed‑rank tests** (RF vs LR, GB vs LR) with Bonferroni‑adjusted α = 0.025 per test.  
10. Generates feature‑importance CSV and PNG (`reports/feature_importance_saturation.*`).  
11. Uploads all artifacts as GitHub Actions artifacts.

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
The prediction completes in **≤ 2 seconds** on the CI runner and **conforms to the original JSON schema** (both fields present; `curie_temperature` is `null`).  

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
If a verified open dataset containing Curie temperature becomes **available**, add its download URL to `code/download_datasets.py`, extend the cleaning step, and rerun the pipeline with `--target curie_temperature`. The CLI will then output a numeric value instead of `null`.

---


