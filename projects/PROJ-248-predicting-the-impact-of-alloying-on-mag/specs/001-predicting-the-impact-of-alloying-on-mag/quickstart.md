# Quickstart: Predicting Alloy Magnetic Properties

This guide walks you through a **single CI run** that produces trained surrogate models for **both** saturation magnetization **and** Curie temperature using the public OQMD and Materials Project datasets, evaluates them, generates feature‑importance plots, and exposes a CLI for single‑alloy prediction.

## Prerequisites
- GitHub Actions runner (free tier) **or** a local Linux environment with **Python 3.11**.
- No API keys required (Materials Project bulk archive is publicly downloadable via Zenodo).

## 1. Clone the Repository & Install Dependencies
```bash
git clone 
cd PROJ-248-predicting-the-impact-of-alloying-on-mag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Download the Raw Datasets
```bash
python code/download_datasets.py
```

This step creates the following files under `data/`:
- `raw_mp.jsonl` – filtered Materials Project magnetic entries
- `raw_oqmd.csv` – OQMD magnetic CSV
- `data_sources.yaml` – manifest with version identifiers and SHA‑256 checksums

## 3. Run the End‑to‑End Pipeline
```bash
python -m src.models.train \
    --targets saturation_magnetization curie_temperature \
    --datasets oqmd mp \
    --output_dir artifacts \
    --log_dir logs
```
**What happens**
1. Downloads the OQMD CSV from the verified Hugging Face URL.  
2. Downloads the Materials Project bulk archive (Zenodo DOI ``) and streams it to avoid full‑disk extraction.  
3. Cleans the combined dataset, discarding records missing required fields and resolving duplicates.  
4. Engineers features (elemental fractions, elemental‑average properties, crystal descriptors, **optional DFT metadata**).  
5. Performs a 5‑fold GridSearchCV (≤ 30 min per target) for Random Forest and Gradient Boosting.  
6. Saves the best model for each target as `artifacts/model_saturation.pkl` and `artifacts/model_curie.pkl`.  
7. Writes `metrics/metrics_saturation.json` and `metrics/metrics_curie.json` (R², MAE, RMSE).  
8. Generates feature‑importance bar charts (`reports/feature_importance_saturation.png`, `reports/feature_importance_curie.png`) and CSV exports.  
9. Conducts paired Wilcoxon signed‑rank tests for both targets and logs Bonferroni‑corrected p‑values.  
10. Uploads all artifacts as GitHub Actions artifacts.

## 4. Inspect Results
```bash
# Metrics
cat metrics/metrics_saturation.json
cat metrics/metrics_curie.json

# Feature‑importance plot
display reports/feature_importance_saturation.png
display reports/feature_importance_curie.png
```

## 5. Single‑Alloy Prediction (CLI)
Create a JSON file `example_alloy.json`:
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

The output `prediction.json` will contain:
```json
{
  "saturation_magnetization": "characteristic value to be determined during the experimental phase",
  "curie_temperature": "high (significantly above room temperature)",
  "confidence_interval": {
    "saturation_magnetization": ["low-end estimate", 1.36],
    "curie_temperature": ["lower bound of the expected range", 660.0]
  }
}
```
This conforms to `contracts/prediction.schema.yaml` and is produced in **≤ 2 seconds** on the CI runner.

## 6. Artifact Publishing (GitHub Actions)
The workflow `ci.yml` automatically uploads the following as artifacts:
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

## 7. Extending to New Targets
If additional magnetic properties become available in future releases (e.g., anisotropy), simply add them to the `--targets` argument; the pipeline will automatically handle feature generation and model training.
