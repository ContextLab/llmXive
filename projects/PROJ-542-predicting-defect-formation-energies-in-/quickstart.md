# Quickstart: Predicting Defect Formation Energies in Perovskites

> All commands assume you are running inside the repository root on a fresh runner with Python 3.11 installed.

## 1️⃣ Setup
```bash
# Create a fresh virtual environment
python -m venv.venv
source.venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2️⃣ Provide the Dataset
- **Option A (automatic)**: Export your Materials Project API key:
 ```bash
 export MP_API_KEY="YOUR_API_KEY"
 ```
 The pipeline will download the defect dataset automatically. [UNRESOLVED-CLAIM: c_be90c46f — status=not_enough_info]
- **Option B (manual)**: Place a CSV file named `materials_defects.csv` in `data/raw/`. The file must conform to the `raw_dataset.schema.yaml` (see `contracts/`). Compute its SHA‑256 checksum:
 ```bash
 sha256sum data/raw/materials_defects.csv > data/raw/materials_defects.csv.sha256
 ```

## 3️⃣ Run the Full Pipeline
```bash
python -m src.pipeline.run
```
The command will execute the end‑to‑end workflow and, upon successful completion, print:

```
Pipeline completed successfully
```

## 4️⃣ Run Individual Scripts (alternative)
```bash
# 4.1 Feature engineering
python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv

# 4.2 Model training (CV)
python -m src.train data/processed/features.csv data/processed/cv_metrics.json

# 4.3 Evaluation on held‑out test set
python -m src.evaluate data/processed/features.csv data/processed/performance.json
```

## 5️⃣ Validate Contracts
```bash
pytest -q
```
All tests should pass, confirming that the CSV and JSON artefacts match their schemas. [UNRESOLVED-CLAIM: c_6429c918 — status=not_enough_info]

## 6️⃣ Inspect Results
- **Performance summary**: `cat data/processed/performance.json | jq`
- **Scatter plot**: open `figures/pred_vs_actual.png`
- **Feature importance**: open `figures/feature_importance.png`

## 7️⃣ Re‑run with a Different Random Seed (optional)
```bash
export RANDOM_SEED=123
python -m src.pipeline.run
```

> The Quickstart guide satisfies **FR‑010**, ensuring the entire workflow can be reproduced by a new researcher.
