# Quickstart: Predicting Defect Formation Energies in Perovskites

> All commands assume you are running inside the repository root on a fresh GitHub Actions (or local) runner with Python 3.11 installed.

## 1️⃣ Setup
```bash
# Create a fresh virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2️⃣ Provide the Dataset
- **Option A (automatic)**: Export your Materials Project API key:
  ```bash
  export MP_API_KEY="YOUR_API_KEY"
  ```
  The pipeline will download the defect dataset automatically.
- **Option B (manual)**: Place a CSV file named `materials_defects.csv` in `data/raw/`. The file must conform to the `raw_dataset.schema.yaml` contract (see `contracts/`). Compute its SHA‑256 checksum **immediately after placement**:
  ```bash
  sha256sum data/raw/materials_defects.csv > data/checksums/raw_defects.sha256
  ```

## 3️⃣ Run the Full Notebook (recommended)
```bash
# Measure total runtime with the built‑in time command
time jupyter nbconvert --to notebook --execute src/pipeline.ipynb --output pipeline_executed.ipynb
```
The notebook will:
1. Verify the dataset checksum.  
2. Compute the twelve compositional descriptors (radius, electronegativity, oxidation state, valence electron count for A, B, X). Missing descriptor values are logged to `descriptor_gaps.log`; the run aborts if any gaps are found (FR‑006).  
3. Perform an 80/20 stratified (by composition) train‑test split.  
4. Run 5‑fold **GroupKFold** cross‑validation on the training split.  
5. Select the best model, evaluate on the held‑out test set, and produce:
   - `data/processed/performance.json`  
   - `figures/pred_vs_actual.png`  
   - `figures/feature_importance.png`  

The total wall‑clock time is printed by `time`; the pipeline will abort automatically if it exceeds **30 minutes** (SC‑004).

## 4️⃣ Run Individual Scripts (alternative)
```bash
# 4.1 Feature engineering
python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv

# 4.2 Verify checksum for the engineered features
sha256sum data/processed/features.csv > data/checksums/features.sha256

# 4.3 Validate dataset size and descriptor completeness
python -m src.validate data/processed/features.csv

# 4.4 Split train/test
python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv

# 4.5 Train/validate (CV) – operates on train.csv only
python -m src.train data/processed/train.csv data/processed/cv_metrics.json

# 4.6 Final evaluation
python -m src.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json
```

## 5️⃣ Validate Contracts
```bash
pytest -q
```
All tests should pass, confirming that the CSV and JSON artefacts match their schemas (`raw_dataset.schema.yaml`, `model_performance.schema.yaml`).

## 6️⃣ Inspect Results
- **Performance summary**: `cat data/processed/performance.json | jq`  
- **Scatter plot**: open `figures/pred_vs_actual.png`  
- **Feature importance**: open `figures/feature_importance.png`

## 7️⃣ Re‑run with a Different Random Seed (optional)
```bash
export RANDOM_SEED=123
time jupyter nbconvert --to notebook --execute src/pipeline.ipynb --output pipeline_executed.ipynb
```

> The Quickstart guide satisfies **FR‑010**, ensuring the entire workflow can be reproduced by a new researcher.

---

