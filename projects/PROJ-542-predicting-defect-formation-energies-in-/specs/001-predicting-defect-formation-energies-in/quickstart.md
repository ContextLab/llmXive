# Quickstart: Predicting Defect Formation Energies in Perovskites

> All commands assume you are running inside the repository root on a fresh GitHub Actions runner (or a local Linux environment) with Python 3.11 installed.

## 1️⃣ Setup the Python environment
```bash
# Create a clean virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2️⃣ Provide the dataset
The pipeline needs a CSV with the columns `composition`, `defect_type`, and `formation_energy`.  

- **Option A – Automatic download** (requires a Materials Project API key):
  ```bash
  export MP_API_KEY="YOUR_API_KEY"
  ```
  The notebook will attempt to fetch the data. If the key is missing or the API returns no records, the run will abort with a clear error (see FR‑007).  

- **Option B – Manual upload** (recommended for CI):
  1. Place your CSV at `data/raw/materials_defects.csv`.  
  2. Verify it matches the schema:
     ```bash
     pip install jsonschema
     python - <<'PY'
import json, jsonschema, pandas as pd
schema = json.load(open('contracts/raw_dataset.schema.yaml'))
df = pd.read_csv('data/raw/materials_defects.csv')
# Validate each row (only a subset needed for schema check)
jsonschema.validate(instance=df.to_dict(orient='records')[0], schema=schema)
PY
     ```
  3. Record its checksum (required for data‑hygiene):
     ```bash
     sha256sum data/raw/materials_defects.csv > data/checksums/raw_defects.sha256
     ```

## 3️⃣ Run the full pipeline (recommended)
```bash
# Measure total runtime; the pipeline will abort if >30 min
time jupyter nbconvert --to notebook --execute src/pipeline.ipynb --output pipeline_executed.ipynb
```
The notebook will:
1. Verify the raw CSV checksum.  
2. Compute the twelve compositional descriptors (radius, electronegativity, oxidation state, valence electron count for A, B, X) – rows with missing oxidation states are dropped according to the predefined filtering criteria.  
3. Capture any DFT functional / temperature / pressure metadata (confounder log).  
4. Perform an 80/20 stratified split by composition **and** create a [deferred] validation split (used only for fallback).  
5. Run 5‑fold GroupKFold CV for Random Forest and Gradient Boosting.  
6. Select the best model, evaluate on the held‑out test set, and produce:
   - `data/processed/performance.json`  
   - `figures/pred_vs_actual.png`  
   - `figures/feature_importance.png`  

If the baseline model does **not** achieve **RMSE ≤ 0.5 eV** and **R² ≥ 70 %**, the notebook automatically augments the feature matrix with structural descriptors (if a `structure_cif` column is present) and re‑runs training/evaluation using the **validation.csv** as the held‑out set (FR‑012).  

## 4️⃣ Run the pipeline step‑by‑step (alternative)
```bash
# 4.1 Feature engineering
python -m src.data.featurize data/raw/materials_defects.csv data/processed/features.csv

# 4.2 Verify checksum for the engineered features
sha256sum data/processed/features.csv > data/checksums/features.sha256

# 4.3 Validate dataset size and descriptor completeness
#   - Requires at least 50 samples for any CV (hard minimum, FR‑009)
#   - Issues a power‑size warning if < 500 samples (see Power‑analysis justification)
python -m src.data.validate data/processed/features.csv

# 4.4 Split train/test/validation
python -m src.data.split data/processed/features.csv data/processed/train.csv data/processed/test.csv data/processed/validation.csv

# 4.5 Generate checksums for splits
sha256sum data/processed/train.csv > data/checksums/train.sha256
sha256sum data/processed/test.csv > data/checksums/test.sha256
sha256sum data/processed/validation.csv > data/checksums/validation.sha256

# 4.6 Train/validate (CV) – operates on train.csv only
python -m src.models.train data/processed/train.csv data/processed/cv_metrics.json

# 4.7 Final evaluation (includes bootstrap CI and t‑test)
python -m src.models.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json

# 4.8 (Optional) Fallback augmentation if baseline fails
python -m src.models.fallback data/processed/train.csv data/processed/validation.csv data/processed/features_augmented.csv data/processed/performance.json

# 4.9 (Optional) Confounder integration
# If metadata.json contains usable fields, merge them as extra covariates:
python -m src.models.confounder_integration data/processed/train.csv data/raw/metadata.json data/processed/train_with_confounders.csv
```

## 5️⃣ Validate contracts
```bash
pytest -q
```
All tests should pass, confirming that:
- CSV files validate against their schemas (`raw_dataset.schema.yaml`, `features.schema.yaml`).
- JSON performance reports validate against `model_performance.schema.yaml`.
- Checksums match the recorded files.
- The runtime log respects the allocated time budget. (SC‑004).

## 6️⃣ Inspect results
```bash
# Human‑readable summary
cat data/processed/performance.json | jq

# Visual checks
display figures/pred_vs_actual.png
display figures/feature_importance.png
```

## 7️⃣ Re‑run with a different random seed (optional)
```bash
export RANDOM_SEED=123
time jupyter nbconvert --to notebook --execute src/pipeline.ipynb --output pipeline_executed.ipynb
```

> The Quickstart satisfies **FR‑010** (end‑to‑end reproducible notebook) and **SC‑004** (runtime budget) while respecting the Constitution’s reproducibility and data‑hygiene requirements, and now explicitly enforces the **≥ 500‑sample** validation threshold, logs a **power‑size warning** when the dataset is under‑powered, and documents the optional confounder integration step.  

---


