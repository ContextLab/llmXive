# Quickstart: Predicting Molecular Packing Efficiency from SMILES

This guide walks you through reproducing the full end‑to‑end analysis on a fresh GitHub Actions (or local) runner.

## Prerequisites
- Python 3.11 installed (or use the provided `setup.sh` script).  
- Git installed.  
- Internet access (to download COD archive and the SMILES‑Transformer model).

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/PROJ-511-packing-efficiency.git
cd PROJ-511-packing-efficiency
```

## 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins all versions
```

## 3. Download & Extract COD Data
```bash
python src/pipelines/download_cod.py
# Output: data/raw/cod_YYYYMMDD.tar.gz  (checksum recorded automatically)
```

## 4. Prepare the Curated Dataset
```bash
python src/pipelines/prepare_dataset.py
# Generates:
#   data/processed/dataset.csv
#   data/processed/fingerprints.npy (optional)
#   logs/pipeline.log
```

## 5. Generate Fingerprints (SMILES‑Transformer)
```bash
python src/pipelines/fingerprint.py
# Updates `fingerprint` column in `dataset.csv`.
```

## 6. Split, Train, and Save the Model
```bash
python src/pipelines/train.py
# Artifacts:
#   models/model.pt
#   logs/training.log
```

## 7. Evaluate on Validation Set
```bash
python src/pipelines/evaluate.py
# Produces:
#   figures/scatter_pred_true.png
#   figures/residuals.png
#   report.txt  (human‑readable)
```

## 8. Statistical Significance & Sensitivity
```bash
python src/pipelines/significance.py
# Appends permutation test results and sensitivity sweep to `report.txt`.
```

## 9. Verify Contracts (Optional)
```bash
pytest -q
# Checks:
#   - `dataset.csv` conforms to `contracts/dataset.schema.yaml`
#   - `model.pt` conforms to `contracts/model.schema.yaml`
```

## Expected Outputs
- `data/processed/dataset.csv` with ≥ 500 rows and required columns.  
- `models/model.pt` (≤ 2 MB).  
- `figures/` containing at least two PNG diagnostics.  
- `report.txt` containing all metrics:
  - **Pearson r** ≥ 0.4 (predictive) **or** < 0.2 (null finding) – per **SC‑001**.  
  - **MAE** ≤ 0.05 – per **SC‑002**.  
  - **Permutation‑test p‑value** < 0.05 – per **SC‑003**.  
  - **Sensitivity analysis** shows unchanged significance for α = 0.01, 0.05, 0.10 – per **SC‑004**.  
  - **Diagnostics**: Shapiro‑Wilk p > 0.05, no heteroscedasticity, Spearman ρ ≥ 0.4 – per **SC‑006**.  

If any step fails, consult `logs/pipeline.log` for detailed warnings (e.g., CIFs missing unit‑cell parameters, SMILES generation failures, early‑stopping warnings).

---


