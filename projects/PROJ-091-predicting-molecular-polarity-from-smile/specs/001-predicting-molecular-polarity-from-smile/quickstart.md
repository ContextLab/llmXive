# Quickstart: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Prerequisites
- Python 3.11 or newer  
- `git`  
- Internet access (to download QM9 via `qm9pack`)  
- ≤ 6 GB RAM, ≥ 14 GB disk space (GitHub Actions free tier)

## Installation

```bash
# 1. Clone the repository
git clone 
cd predict-molecular-polarity

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install exact dependencies
pip install -r requirements.txt
```

`requirements.txt` pins versions of `rdkit`, `lightgbm`, `shap`, `pandas`, `numpy`, `scikit-learn`, `qm9pack`, `pytest`, and `scipy`.

## Running the Full Pipeline

All steps are orchestrated via `code/main.py`. Each step can be run independently or in sequence.

| Step | Command | Output |
|------|---------|--------|
| 1️⃣ Fetch & preprocess | `python code/main.py --step fetch_and_preprocess` | `data/raw/qm9_raw.parquet`, `data/processed/descriptors.parquet` |
| 2️⃣ Feature selection | `python code/main.py --step feature_selection` | `data/processed/vif_scores.csv`, `data/processed/cluster_map.csv` |
| 3️⃣ Train model | `python code/main.py --step train` | `data/processed/model.pkl`, `data/results/training_metrics.json` |
| 4️⃣ Analyse & validate | `python code/main.py --step analyze` | `data/results/shap_summary.png`, `data/results/stability_report.json` |
| 5️⃣ Verify reproducibility | `python code/main.py --step verify` | Pass/Fail checksum report (validated against contracts) |

### Example Full Run

```bash
python code/main.py --step fetch_and_preprocess
python code/main.py --step feature_selection
python code/main.py --step train
python code/main.py --step analyze
python code/main.py --step verify
```

The **verify** step runs `code/data/validate.py`, which checks each generated artifact against its corresponding contract schema (see the Contract Validation Mapping table in `plan.md`/`data-model.md`) and compares SHA‑256 checksums recorded in `state/manifest.json`.

## Testing

```bash
pytest tests/ -v
```

Key test groups:

- **Unit** (`tests/unit/`): descriptor generation, VIF computation, 3‑D function guard.  
- **Contract** (`tests/contract/`): schema validation against `contracts/descriptor_schema.schema.yaml`, `contracts/vif_schema.schema.yaml`, etc.  
- **Integration** (`tests/integration/`): end‑to‑end pipeline sanity check.

## Troubleshooting

- **MemoryError**: Reduce `BATCH_SIZE` in `code/data/preprocess.py` or lower the bootstrap subsample size.  
- **NaN warnings**: Check `logs/preprocess.log`; records with > 5 % missing descriptors are dropped automatically.  
- **3‑D leakage detected**: The unit test `test_no_3d_generation` will fail; ensure no import of `AllChem.EmbedMolecule` or `Get3DConformer`.  
- **VIF fallback triggered**: Inspect `data/processed/vif_scores.csv` – column `fallback_triggered` will be `True`. The pipeline then uses L1‑regularized LightGBM.  

---

