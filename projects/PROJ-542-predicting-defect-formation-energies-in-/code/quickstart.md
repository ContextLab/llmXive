# Quickstart: Predicting Defect Formation Energies in Perovskites

> All commands assume you are running inside the repository root on a fresh GitHub Actions (or local) runner with Python 3.11 installed.

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
 The pipeline will download the defect dataset automatically.
- **Option B (manual)**: Place a CSV file named `materials_defects.csv` in `data/raw/`. The file must conform to the `raw_dataset.schema.yaml` (see `contracts/`). Compute its SHA‑256 checksum **immediately after placement**:
 ```bash
 sha256sum data/raw/materials_defects.csv > data/checksums/raw_defects.sha256
 ```

## 3️⃣ Run the Full Pipeline (single command)
```bash
python -m src.pipeline.run
```
The command will execute the end‑to‑end workflow (download, checksum, featurization, descriptor‑gap check, validation, train/test split, 5‑fold GroupKFold cross‑validation, evaluation, and figures) and, upon successful completion, print:

```
Pipeline completed successfully
```

This is the exact command asserted by the CI test `src/tests/test_quickstart.py`, satisfying FR‑010 and SC‑004.

## 4️⃣ Run Individual Scripts (alternative)
```bash
# 4.1 Feature engineering
python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv

# 4.2 Train/test split (deterministic 80/20, group‑disjoint)
python -m src.models.split data/processed/features.csv data/processed/train.csv data/processed/test.csv

# 4.3 Model training (5‑fold GroupKFold CV)
python -m src.models.train data/processed/features.csv data/processed/cv_metrics.json

# 4.4 Evaluation on held‑out test set
python -m src.models.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json
```

## 5️⃣ Validate Contracts
```bash
pytest -q
```
All tests should pass, confirming that the CSV and JSON artefacts match their schemas. [UNRESOLVED-CLAIM: c_088600f4 — status=not_enough_info]

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