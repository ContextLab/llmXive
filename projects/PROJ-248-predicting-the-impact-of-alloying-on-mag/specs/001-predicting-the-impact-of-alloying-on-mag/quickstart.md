# Quickstart: Predicting Alloy Magnetic Properties

This guide walks you through a **single CI run** that produces a trained surrogate model for **saturation magnetization** using the public OQMD dataset, evaluates it, generates feature‑importance plots, and exposes a CLI for single‑alloy prediction.

## Prerequisites
- GitHub Actions runner (free tier) or a local Linux environment with **Python 3.11**.
- No API keys required (Materials Project data is not used in this quickstart).

## 1. Clone the Repository & Install Dependencies
```bash
git clone https://github.com/your-org/PROJ-248-predicting-the-impact-of-alloying-on-mag.git
cd PROJ-248-predicting-the-impact-of-alloying-on-mag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the End‑to‑End Pipeline
```bash
python -m src.models.train \
    --targets saturation_magnetization \
    --dataset oqmd \
    --output_dir artifacts \
    --log_dir logs
```
- **What happens**  
  1. Downloads OQMD CSV from the verified Hugging Face URL.  
  2. Cleans the data, discarding records missing `magnetic_moment` (none for saturation).  
  3. Engineers features (elemental fractions + crystal descriptors).  
  4. Performs a 5‑fold GridSearchCV (≤ 30 min) for Random Forest and Gradient Boosting.  
  5. Saves the best model as `artifacts/model_saturation.pkl`.  
  6. Writes `metrics/metrics_saturation.json` (R², MAE, RMSE) and `reports/feature_importance_saturation.csv` + `reports/feature_importance_saturation.png`.  

## 3. Inspect Results
```bash
# Metrics
cat metrics/metrics_saturation.json

# Feature importance plot
display reports/feature_importance_saturation.png
```

## 4. Single‑Alloy Prediction (CLI)
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
python -m src.cli.predict --model artifacts/model_saturation.pkl \
    --input example_alloy.json --output prediction.json
```

The output `prediction.json` will contain:
```json
{
  "saturation_magnetization": 1.23,
  "curie_temperature": null,
  "confidence_interval": {
    "saturation_magnetization": [1.10, 1.36],
    "curie_temperature": [null, null]
  }
}
```
This conforms to the updated `contracts/prediction.schema.yaml` and will be produced in **≤ 2 seconds** on the CI runner.

## 5. Artifact Publishing (GitHub Actions)
The workflow `ci.yml` automatically uploads the following as artifacts:
- `data/cleaned_oqmd.csv`
- `artifacts/model_saturation.pkl`
- `metrics/metrics_saturation.json`
- `reports/feature_importance_saturation.*`
- `contracts/prediction.schema.yaml`

These artifacts enable reproducibility checks by downstream reviewers.

## 6. Extending to Curie Temperature (Future Work)
When an open dataset containing `curie_temperature` becomes available, repeat step 2 with `--targets curie_temperature`. The same pipeline will handle both targets automatically.

---


