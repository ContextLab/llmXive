# Quickstart: Predicting Defect Formation Energies in Perovskites

> All commands assume you are running inside the repository root on a fresh GitHub Actions (or local) runner with Python 3.11 installed.

## 1️⃣ Setup
```bash
# Create a fresh virtual environment
python -m venv.venv
source.venv/bin/activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 2️⃣ Provide the Dataset
- **Option A (automatic)**: Export your Materials Project API key:
 ```bash
 export MP_API_KEY="YOUR_API_KEY"
 ```
 The pipeline will download the defect dataset automatically.
- **Option B (manual)**: Place a CSV file named `materials_defects.csv` in `data/raw/`. The file must conform to the `raw_dataset.schema.yaml` contract (see `contracts/`). Compute its SHA-256 checksum:
 ```bash
 sha256sum data/raw/materials_defects.csv > data/checksums/raw_defects.sha256
 ```

## 3️⃣ Run the Full Pipeline
```bash
python -m code.pipeline.run
```
The command executes the end-to-end workflow:
1. **Data Acquisition**: Downloads perovskite defect data.
2. **Featurization**: Computes 12 compositional descriptors via `pymatgen` [UNRESOLVED-CLAIM: c_00eaf5ae — status=not_enough_info].
3. **Validation**: Checks dataset size and descriptor completeness.
4. **Splitting**: Performs a deterministic 80/20 group-aware split.
5. **Training**: Runs 5-fold GroupKFold CV for Random Forest and Gradient Boosting.
6. **Evaluation**: Computes RMSE, MAE, R², and produces performance plots.

## 4️⃣ Run Individual Scripts (alternative)
```bash
# 4.1 Feature engineering
python -m code.data.featurize data/raw/materials_defects.csv data/processed/features.csv

# 4.2 Train/test split
python -m code.models.split data/processed/features.csv data/processed/train.csv data/processed/test.csv

# 4.3 Model training
python -m code.models.train data/processed/train.csv data/processed/cv_metrics.json

# 4.4 Evaluation
python -m code.models.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json
```

## 5️⃣ Validate Contracts
```bash
pytest -q
```

## 6️⃣ Inspect Results
- **Performance summary**: `cat data/processed/performance.json | jq`
- **Scatter plot**: `figures/pred_vs_actual.png`
- **Feature importance**: `figures/feature_importance.png`
